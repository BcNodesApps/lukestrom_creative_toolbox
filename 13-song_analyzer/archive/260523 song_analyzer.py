#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
song_analyzer.py
Watches INPUT_DIR for new audio files (.wav/.mp3/.flac/.m4a/.aac/.ogg),
analyzes them, and writes a SINGLE self-contained PDF report into OUTPUT_DIR,
then (optionally) deletes the processed input file.

Settings come from .env in the SAME FOLDER.

Requires:
- numpy, librosa, matplotlib
- reportlab (for PDF)
- pyloudnorm (optional; for LUFS, if missing LUFS will be 'n/a')
"""

import os
import time
import math
import io
from pathlib import Path

# --- Load .env from the same directory as this script ---------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
ENV_PATH = SCRIPT_DIR / ".env"


def _parse_env_line(line: str):
    s = line.strip()
    if not s or s.startswith("#") or "=" not in s:
        return None
    key, val = s.split("=", 1)
    if "#" in val:
        val = val.split("#", 1)[0]
    return key.strip(), val.strip()


def load_env(path: Path) -> None:
    if path.exists():
        for raw in path.read_text(encoding="utf-8").splitlines():
            parsed = _parse_env_line(raw)
            if parsed:
                k, v = parsed
                os.environ.setdefault(k, v)


load_env(ENV_PATH)

# --- Config ----------------------------------------------------------------------------
INPUT_DIR = os.getenv("INPUT_DIR", r"D:\OneDrive\Production\creations\music\analysis\input")
WORK_DIR = os.getenv("WORK_DIR", r"D:\OneDrive\Production\creations\music\analysis\work")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", r"D:\OneDrive\Production\creations\music\analysis\output")
DELETE_AFTER = os.getenv("DELETE_AFTER", "true").lower() in ("1", "true", "yes")
MIN_STABLE_SECONDS = float(os.getenv("MIN_STABLE_SECONDS", "3.0"))

for p in (INPUT_DIR, WORK_DIR, OUTPUT_DIR):
    Path(p).mkdir(parents=True, exist_ok=True)

# --- Dependencies (NumPy/librosa compatibility guards) --------------------------------
import numpy as _np  # noqa: E402

if not hasattr(_np, "complex"):
    _np.complex = complex  # type: ignore[attr-defined]
if not hasattr(_np, "float"):
    _np.float = float  # type: ignore[attr-defined]
if not hasattr(_np, "int"):
    _np.int = int  # type: ignore[attr-defined]

import numpy as np  # noqa: E402
import librosa  # noqa: E402

try:
    import pyloudnorm as pyln  # noqa: E402
except Exception:
    pyln = None  # type: ignore[assignment]

# Headless plotting
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# PDF (required)
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle

# --- Analysis settings -----------------------------------------------------------------
BANDS = [
    ("Sub", 20, 60),
    ("Bass", 60, 120),
    ("Low-Mids", 120, 250),
    ("Muddiness", 250, 500),
    ("Mids", 500, 2000),
    ("Presence", 2000, 6000),
    ("Air", 6000, 16000),
]

KEY_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
KK_PROFILE_MAJOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88], dtype=float)
KK_PROFILE_MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17], dtype=float)


def pink_target_db(freqs: np.ndarray) -> np.ndarray:
    """Pink-ish target curve (~ -3 dB/oct), normalized at 1 kHz."""
    with np.errstate(divide="ignore"):
        target = -3.0 * np.log2(np.maximum(freqs, 1e-6) / 1000.0)
    idx_1k = int(np.argmin(np.abs(freqs - 1000.0)))
    target = target - target[idx_1k]
    return target


def moving_average(x: np.ndarray, win: int = 15) -> np.ndarray:
    win = max(3, int(win) | 1)  # odd window >= 3
    pad = win // 2
    xpad = np.pad(x, (pad, pad), mode="edge")
    kernel = np.ones(win, dtype=float) / float(win)
    out = np.convolve(xpad, kernel, mode="same")[pad:-pad]
    return out


def _coerce_tempo_bpm(tempo) -> int | None:
    t = np.asarray(tempo)
    if t.size == 0:
        return None
    first = float(t.flat[0])
    if not np.isfinite(first):
        return None
    return int(round(first))


def _estimate_key(y: np.ndarray, sr: int):
    """Estimate key with chroma + Krumhansl-Kessler profiles. Returns (label, confidence)."""
    try:
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        chroma_mean = chroma.mean(axis=1)
        if not np.isfinite(chroma_mean).all() or np.all(chroma_mean == 0):
            return None, None

        chroma_norm = chroma_mean / (np.linalg.norm(chroma_mean) + 1e-12)
        maj = KK_PROFILE_MAJOR / np.linalg.norm(KK_PROFILE_MAJOR)
        minr = KK_PROFILE_MINOR / np.linalg.norm(KK_PROFILE_MINOR)

        scores = []
        labels = []
        for i in range(12):
            scores.append(float(np.dot(chroma_norm, np.roll(maj, i))))
            labels.append(f"{KEY_NAMES[i]} major")
            scores.append(float(np.dot(chroma_norm, np.roll(minr, i))))
            labels.append(f"{KEY_NAMES[i]} minor")

        scores_arr = np.array(scores)
        best_idx = int(np.argmax(scores_arr))
        best_label = labels[best_idx]
        sorted_scores = np.sort(scores_arr)
        best = float(sorted_scores[-1])
        second = float(sorted_scores[-2]) if scores_arr.size > 1 else 0.0
        denom = float(scores_arr.clip(min=0).sum()) + 1e-9
        confidence = max(0.0, (best - second)) / denom
        return best_label, round(confidence, 3)
    except Exception:
        return None, None


def analyze_file(file_path: str) -> dict:
    # Load mono
    y, sr = librosa.load(file_path, sr=None, mono=True)
    duration = len(y) / float(sr)

    # LUFS-I
    if pyln is not None:
        meter = pyln.Meter(sr)
        loudness = float(meter.integrated_loudness(y.astype(float)))
    else:
        loudness = float("nan")

    # Tempo
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr, trim=True)
    tempo_bpm = _coerce_tempo_bpm(tempo)

    # Key
    key_label, key_conf = _estimate_key(y, sr)

    # Spectrum vs target
    n_fft = 4096
    hop_length = 1024
    S = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=hop_length))
    mean_spec = np.mean(S, axis=1, dtype=float) + 1e-12
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    mean_db = 20.0 * np.log10(mean_spec)
    mean_db_s = moving_average(mean_db, win=15)
    target_db = pink_target_db(freqs)
    deviation = mean_db_s - target_db

    # Per-band suggestions
    band_rows = []
    band_labels = []
    band_devs = []
    for name, f_lo, f_hi in BANDS:
        idx = np.where((freqs >= f_lo) & (freqs < f_hi))[0]
        if idx.size == 0:
            avg_dev = float("nan")
            suggestion = "n/a"
        else:
            avg_dev_val = float(np.mean(deviation[idx]))
            if avg_dev_val > 2.0:
                suggestion = f"Cut ~{round(avg_dev_val, 1)} dB"
            elif avg_dev_val < -2.0:
                suggestion = f"Boost ~{round(-avg_dev_val, 1)} dB"
            else:
                suggestion = "Close to target"
            avg_dev = avg_dev_val

        band_rows.append(
            {
                "Band": name,
                "Range": f"{f_lo}-{f_hi} Hz",
                "AvgDev": "" if math.isnan(avg_dev) else round(avg_dev, 2),
                "EQ": suggestion,
            }
        )
        band_labels.append(name)
        band_devs.append(float("nan") if math.isnan(avg_dev) else float(avg_dev))

    # Tilt
    low_idx = np.where((freqs >= 60) & (freqs < 250))[0]
    high_idx = np.where((freqs >= 2000) & (freqs < 8000))[0]
    low_dev = float(np.mean(deviation[low_idx])) if low_idx.size else 0.0
    high_dev = float(np.mean(deviation[high_idx])) if high_idx.size else 0.0
    tilt_note = (
        "Slightly warm (lows↑ vs highs↓)"
        if (low_dev - high_dev) > 2.0
        else "Slightly bright (highs↑ vs lows↓)"
        if (high_dev - low_dev) > 2.0
        else "Balanced tilt"
    )

    return {
        "file": Path(file_path).name,
        "samplerate": sr,
        "duration_sec": round(duration, 2),
        "lufs_integrated": None if math.isnan(loudness) else round(loudness, 2),
        "tempo_bpm": tempo_bpm,
        "key": key_label,
        "key_confidence": key_conf,
        "tilt_note": tilt_note,
        "bands": band_rows,
        "band_labels": band_labels,
        "band_devs": band_devs,
        "freqs": freqs,
        "mean_db_s": mean_db_s,
        "target_db": target_db,
    }


def _plot_to_png_bytes(fig) -> bytes:
    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=130)
    plt.close(fig)
    return buf.getvalue()


def _build_figures(results: dict) -> tuple[bytes, bytes]:
    # Spectrum vs Target
    fig1 = plt.figure(figsize=(8.5, 4.6))
    plt.semilogx(results["freqs"], results["mean_db_s"], label="Average spectrum (smoothed)")
    plt.semilogx(results["freqs"], results["target_db"], label="Pink target (normalized @1k)")
    plt.title("Spectrum vs Pink Target")
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Level (dB)")
    plt.xlim(20, 20000)
    plt.grid(True, which="both", linestyle=":", alpha=0.4)
    plt.legend()
    png1 = _plot_to_png_bytes(fig1)

    # Per-band deviation bars
    fig2 = plt.figure(figsize=(8.5, 4.6))
    x = np.arange(len(results["band_labels"]))
    vals = np.array(results["band_devs"], dtype=float)
    plt.bar(x, vals)
    plt.xticks(x, results["band_labels"])
    plt.axhline(0.0, linewidth=1)
    plt.title("Per-band Average Deviation from Target (dB)")
    plt.ylabel("Deviation (dB)  [positive = hotter than target]")
    plt.grid(True, axis="y", linestyle=":", alpha=0.4)
    png2 = _plot_to_png_bytes(fig2)

    return png1, png2


def _write_pdf(results: dict, output_pdf: Path) -> None:
    doc = SimpleDocTemplate(str(output_pdf), pagesize=A4, rightMargin=30, leftMargin=30, topMargin=28, bottomMargin=28)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Small", fontSize=9, leading=11))
    styles.add(ParagraphStyle(name="Mono", fontName="Helvetica", fontSize=9, leading=11))

    elements = []

    # Header
    elements.append(Paragraph("Audio Analysis Report", styles["Title"]))
    elements.append(Spacer(1, 4))

    # Summary table (left) as key/values
    lufs_txt = f"{results['lufs_integrated']} LUFS" if results["lufs_integrated"] is not None else "n/a"
    tempo_txt = f"{results['tempo_bpm']} BPM" if results["tempo_bpm"] else "n/a"
    key_txt = results["key"] if results.get("key") else "n/a"
    key_conf = f"{results['key_confidence']:.3f}" if results.get("key_confidence") is not None else "n/a"

    meta_data = [
        ["File", results["file"]],
        ["Duration", f"{results['duration_sec']} s"],
        ["Sample rate", f"{results['samplerate']} Hz"],
        ["Integrated Loudness", lufs_txt],
        ["Tempo", tempo_txt],
        ["Estimated Key", key_txt],
        ["Key Confidence", key_conf],
        ["Tonal Tilt", results["tilt_note"]],
    ]
    meta_tbl = Table(meta_data, hAlign="LEFT", colWidths=[3.5 * cm, 11.5 * cm])
    meta_tbl.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
            ]
        )
    )
    elements.append(meta_tbl)
    elements.append(Spacer(1, 8))

    # Plots
    spec_png, band_png = _build_figures(results)
    spec_img = Image(io.BytesIO(spec_png))
    band_img = Image(io.BytesIO(band_png))
    # scale to page width (rough)
    max_w = 17.0 * cm
    spec_img._restrictSize(max_w, 8.5 * cm)
    band_img._restrictSize(max_w, 8.5 * cm)

    elements.append(Paragraph("Spectrum vs Target", styles["Heading3"]))
    elements.append(spec_img)
    elements.append(Spacer(1, 6))
    elements.append(Paragraph("Per-band Deviation", styles["Heading3"]))
    elements.append(band_img)
    elements.append(Spacer(1, 8))

    # EQ table
    eq_header = [["Band", "Range (Hz)", "Avg Dev (dB)", "EQ Suggestion"]]
    eq_rows = [[r["Band"], r["Range"], r["AvgDev"], r["EQ"]] for r in results["bands"]]
    eq_tbl = Table(eq_header + eq_rows, hAlign="LEFT", colWidths=[3 * cm, 4 * cm, 3 * cm, 7 * cm])
    eq_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                ("ALIGN", (2, 1), (2, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
            ]
        )
    )
    elements.append(Paragraph("Per-band EQ Suggestions", styles["Heading3"]))
    elements.append(eq_tbl)
    elements.append(Spacer(1, 6))
    elements.append(Paragraph("— Automated analysis", styles["Small"]))

    doc.build(elements)


def _write_outputs(results: dict, output_dir: Path, stem: str) -> Path:
    """Write ONLY a single PDF in the output folder."""
    pdf_path = output_dir / f"{stem}_analysis.pdf"
    _write_pdf(results, pdf_path)
    return pdf_path


def process_file(input_file: Path) -> None:
    # Move into WORK_DIR to avoid partial writes
    work_target = Path(WORK_DIR) / input_file.name
    try:
        input_file.replace(work_target)
    except Exception:
        import shutil
        shutil.copy2(input_file, work_target)
        try:
            input_file.unlink(missing_ok=True)
        except Exception:
            pass

    # Analyze
    try:
        results = analyze_file(str(work_target))
    except Exception as e:
        print(f"Analyze error for {work_target.name}: {e}")
        return

    # Write single PDF
    try:
        _write_outputs(results, Path(OUTPUT_DIR), work_target.stem)
        print(f"PDF saved: {Path(OUTPUT_DIR) / (work_target.stem + '_analysis.pdf')}")
    except Exception as e:
        print(f"Write PDF error for {work_target.name}: {e}")

    # Cleanup
    if DELETE_AFTER:
        try:
            work_target.unlink(missing_ok=True)
        except Exception:
            pass


# --- Watcher --------------------------------------------------------------------------
AUDIO_EXTS = {".wav", ".mp3", ".flac", ".m4a", ".aac", ".ogg"}


def watch_loop() -> None:
    seen: set[Path] = set()
    while True:
        try:
            for p in Path(INPUT_DIR).glob("*"):
                if p.is_file() and p.suffix.lower() in AUDIO_EXTS:
                    if p not in seen:
                        time.sleep(MIN_STABLE_SECONDS)  # ensure file fully written
                        seen.add(p)
                        process_file(p)
                        seen.remove(p)  # allow same filename later
        except Exception as e:
            print("Watcher error:", e)
        time.sleep(1.0)


if __name__ == "__main__":
    print("Watching:", INPUT_DIR)
    watch_loop()

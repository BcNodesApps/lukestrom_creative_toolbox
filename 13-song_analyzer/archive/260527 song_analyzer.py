#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
song_analyzer.py

GUI version:
- Drag/drop or select one audio file
- Shows a simple YouTube readiness verdict
- Measures LUFS and True Peak with FFmpeg, matching your PowerShell check
- Shows tempo, key, tonal tilt and EQ notes
- Exports PDF to Downloads by default

Install:
    pip install numpy librosa matplotlib reportlab pyloudnorm tkinterdnd2
"""

import math
import io
import re
import shutil
import subprocess
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import numpy as _np

if not hasattr(_np, "complex"):
    _np.complex = complex
if not hasattr(_np, "float"):
    _np.float = float
if not hasattr(_np, "int"):
    _np.int = int

import numpy as np
import librosa

try:
    import pyloudnorm as pyln
except Exception:
    pyln = None

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except Exception:
    DND_AVAILABLE = False


AUDIO_EXTS = {".wav", ".mp3", ".flac", ".m4a", ".aac", ".ogg"}

# Your machines use the same default FFmpeg location.
# The app also falls back to PATH if needed.
DEFAULT_FFMPEG_PATH = r"C:\ffmpeg\bin\ffmpeg.exe"
FFMPEG_TIMEOUT_SECONDS = 300

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

KK_PROFILE_MAJOR = np.array(
    [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88],
    dtype=float
)

KK_PROFILE_MINOR = np.array(
    [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17],
    dtype=float
)


def get_downloads_folder() -> Path:
    downloads = Path.home() / "Downloads"
    return downloads if downloads.exists() else Path.home()


def pink_target_db(freqs: np.ndarray) -> np.ndarray:
    with np.errstate(divide="ignore"):
        target = -3.0 * np.log2(np.maximum(freqs, 1e-6) / 1000.0)

    idx_1k = int(np.argmin(np.abs(freqs - 1000.0)))
    target = target - target[idx_1k]
    return target


def moving_average(x: np.ndarray, win: int = 15) -> np.ndarray:
    win = max(3, int(win) | 1)
    pad = win // 2
    xpad = np.pad(x, (pad, pad), mode="edge")
    kernel = np.ones(win, dtype=float) / float(win)
    out = np.convolve(xpad, kernel, mode="same")[pad:-pad]
    return out


def coerce_tempo_bpm(tempo) -> int | None:
    t = np.asarray(tempo)

    if t.size == 0:
        return None

    first = float(t.flat[0])

    if not np.isfinite(first):
        return None

    return int(round(first))


def estimate_key(y: np.ndarray, sr: int):
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
        second = float(sorted_scores[-2])

        denom = float(scores_arr.clip(min=0).sum()) + 1e-9
        confidence = max(0.0, best - second) / denom

        return best_label, round(confidence, 3)

    except Exception:
        return None, None


def find_ffmpeg() -> str | None:
    default = Path(DEFAULT_FFMPEG_PATH)

    if default.exists():
        return str(default)

    found = shutil.which("ffmpeg")

    if found:
        return found

    return None


def parse_ffmpeg_loudnorm_output(text: str) -> tuple[float | None, float | None]:
    lufs_match = re.search(r"Input Integrated:\s*([+-]?\d+(?:\.\d+)?)\s+LUFS", text)
    peak_match = re.search(r"Input True Peak:\s*([+-]?\d+(?:\.\d+)?)\s+dBTP", text)

    lufs = round(float(lufs_match.group(1)), 2) if lufs_match else None
    true_peak = round(float(peak_match.group(1)), 2) if peak_match else None

    return lufs, true_peak


def measure_loudness_with_ffmpeg(file_path: str) -> tuple[float | None, float | None, str | None]:
    ffmpeg_path = find_ffmpeg()

    if not ffmpeg_path:
        return None, None, "FFmpeg not found."

    cmd = [
        ffmpeg_path,
        "-hide_banner",
        "-nostats",
        "-i",
        file_path,
        "-filter:a",
        "loudnorm=print_format=summary",
        "-f",
        "null",
        "-",
    ]

    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=FFMPEG_TIMEOUT_SECONDS,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
        )

        combined_output = (completed.stdout or "") + "\n" + (completed.stderr or "")
        lufs, true_peak = parse_ffmpeg_loudnorm_output(combined_output)

        if lufs is None and true_peak is None:
            return None, None, "FFmpeg ran, but loudness values could not be read."

        return lufs, true_peak, None

    except Exception as e:
        return None, None, f"FFmpeg loudness check failed: {e}"


def get_youtube_verdict(lufs, true_peak):
    """
    Practical verdict for YouTube music uploads.

    - Around -14 LUFS is a common streaming reference.
    - Slightly louder can still be fine; YouTube may turn it down.
    - True Peak should ideally stay at or below -1.0 dBTP for streaming.
    """

    if lufs is None:
        return "UNKNOWN", "LUFS could not be measured."

    loudness_ok = -15.5 <= lufs <= -12.0
    loud_but_usable = -12.0 < lufs <= -9.0
    quiet_but_usable = -18.0 <= lufs < -15.5
    too_loud = lufs > -9.0
    too_quiet = lufs < -18.0

    peak_ok = true_peak is not None and true_peak <= -1.0
    peak_warning = true_peak is not None and true_peak > -1.0

    if peak_warning:
        if true_peak > 0:
            return "FIX TRUE PEAK", "Loudness is usable, but True Peak is above 0 dBTP. Lower the limiter ceiling."
        return "PEAK TOO HIGH", "Loudness is usable, but True Peak should ideally be -1.0 dBTP or lower."

    if loudness_ok and peak_ok:
        return "GOOD FOR YOUTUBE", "Loudness and True Peak are in a safe practical range."

    if loud_but_usable and peak_ok:
        return "LOUD BUT USABLE", "YouTube may turn it down, but True Peak is safe."

    if quiet_but_usable and peak_ok:
        return "A BIT QUIET", "Probably usable, but it may feel softer than other tracks."

    if too_loud and peak_ok:
        return "TOO LOUD", "Risk of sounding crushed or being reduced heavily by YouTube."

    if too_quiet and peak_ok:
        return "TOO QUIET", "Likely too soft for YouTube. Consider mastering louder."

    if true_peak is None:
        return "LOUDNESS CHECK ONLY", "LUFS was measured, but True Peak could not be measured."

    return "CHECK MASTER", "The measured values need review."


def analyze_file(file_path: str) -> dict:
    y, sr = librosa.load(file_path, sr=None, mono=True)
    duration = len(y) / float(sr)

    # Loudness is measured with FFmpeg so it matches your PowerShell loudnorm check.
    lufs_value, true_peak_value, loudness_error = measure_loudness_with_ffmpeg(file_path)
    verdict, verdict_note = get_youtube_verdict(lufs_value, true_peak_value)

    if loudness_error:
        verdict_note = f"{verdict_note} {loudness_error}"

    tempo, _ = librosa.beat.beat_track(y=y, sr=sr, trim=True)
    tempo_bpm = coerce_tempo_bpm(tempo)

    key_label, key_conf = estimate_key(y, sr)

    n_fft = 4096
    hop_length = 1024

    S = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=hop_length))
    mean_spec = np.mean(S, axis=1, dtype=float) + 1e-12

    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    mean_db = 20.0 * np.log10(mean_spec)
    mean_db_s = moving_average(mean_db, win=15)

    target_db = pink_target_db(freqs)
    deviation = mean_db_s - target_db

    band_rows = []
    band_labels = []
    band_devs = []

    for name, f_lo, f_hi in BANDS:
        idx = np.where((freqs >= f_lo) & (freqs < f_hi))[0]

        if idx.size == 0:
            avg_dev = float("nan")
            suggestion = "n/a"
        else:
            avg_dev = float(np.mean(deviation[idx]))

            if avg_dev > 2.0:
                suggestion = f"Cut about {round(avg_dev, 1)} dB"
            elif avg_dev < -2.0:
                suggestion = f"Boost about {round(-avg_dev, 1)} dB"
            else:
                suggestion = "Close to target"

        band_rows.append({
            "Band": name,
            "Range": f"{f_lo}-{f_hi} Hz",
            "AvgDev": "" if math.isnan(avg_dev) else round(avg_dev, 2),
            "EQ": suggestion,
        })

        band_labels.append(name)
        band_devs.append(float("nan") if math.isnan(avg_dev) else float(avg_dev))

    low_idx = np.where((freqs >= 60) & (freqs < 250))[0]
    high_idx = np.where((freqs >= 2000) & (freqs < 8000))[0]

    low_dev = float(np.mean(deviation[low_idx])) if low_idx.size else 0.0
    high_dev = float(np.mean(deviation[high_idx])) if high_idx.size else 0.0

    if (low_dev - high_dev) > 2.0:
        tilt_note = "Slightly warm: lows stronger than highs"
    elif (high_dev - low_dev) > 2.0:
        tilt_note = "Slightly bright: highs stronger than lows"
    else:
        tilt_note = "Balanced tilt"

    return {
        "file_path": file_path,
        "file": Path(file_path).name,
        "samplerate": sr,
        "duration_sec": round(duration, 2),
        "lufs_integrated": lufs_value,
        "true_peak": true_peak_value,
        "youtube_verdict": verdict,
        "youtube_note": verdict_note,
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


def build_spectrum_figure(results: dict):
    fig = plt.Figure(figsize=(7.5, 3.4), dpi=100)
    ax = fig.add_subplot(111)

    ax.semilogx(results["freqs"], results["mean_db_s"], label="Average spectrum")
    ax.semilogx(results["freqs"], results["target_db"], label="Reference curve")

    ax.set_title("Tone Balance Reference")
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Level")
    ax.set_xlim(20, 20000)
    ax.grid(True, which="both", linestyle=":", alpha=0.4)
    ax.legend()

    fig.tight_layout()
    return fig


def build_band_figure(results: dict):
    fig = plt.Figure(figsize=(7.5, 3.2), dpi=100)
    ax = fig.add_subplot(111)

    x = np.arange(len(results["band_labels"]))
    vals = np.array(results["band_devs"], dtype=float)

    ax.bar(x, vals)
    ax.set_xticks(x)
    ax.set_xticklabels(results["band_labels"])
    ax.axhline(0.0, linewidth=1)
    ax.set_title("EQ Balance Check")
    ax.set_ylabel("Difference from reference")
    ax.grid(True, axis="y", linestyle=":", alpha=0.4)

    fig.tight_layout()
    return fig


def figure_to_png_bytes(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130)
    return buf.getvalue()


def write_pdf(results: dict, output_pdf: Path) -> None:
    doc = SimpleDocTemplate(
        str(output_pdf),
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=28,
        bottomMargin=28
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Small", fontSize=9, leading=11))

    elements = []

    elements.append(Paragraph("Audio Analysis Report", styles["Title"]))
    elements.append(Spacer(1, 6))

    lufs_txt = f"{results['lufs_integrated']} LUFS" if results["lufs_integrated"] is not None else "n/a"
    true_peak_txt = f"{results['true_peak']} dBTP" if results.get("true_peak") is not None else "n/a"
    tempo_txt = f"{results['tempo_bpm']} BPM" if results["tempo_bpm"] else "n/a"
    key_txt = results["key"] if results.get("key") else "n/a"
    key_conf = f"{results['key_confidence']:.3f}" if results.get("key_confidence") is not None else "n/a"

    meta_data = [
        ["YouTube Verdict", results["youtube_verdict"]],
        ["Verdict Note", results["youtube_note"]],
        ["File", results["file"]],
        ["Duration", f"{results['duration_sec']} s"],
        ["Sample rate", f"{results['samplerate']} Hz"],
        ["Integrated Loudness", lufs_txt],
        ["True Peak", true_peak_txt],
        ["Tempo", tempo_txt],
        ["Estimated Key", key_txt],
        ["Key Confidence", key_conf],
        ["Tonal Tilt", results["tilt_note"]],
    ]

    meta_tbl = Table(meta_data, hAlign="LEFT", colWidths=[4 * cm, 11 * cm])
    meta_tbl.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
        ("BACKGROUND", (0, 0), (-1, 1), colors.HexColor("#e8f5e9")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))

    elements.append(meta_tbl)
    elements.append(Spacer(1, 8))

    spec_fig = build_spectrum_figure(results)
    band_fig = build_band_figure(results)

    spec_img = Image(io.BytesIO(figure_to_png_bytes(spec_fig)))
    band_img = Image(io.BytesIO(figure_to_png_bytes(band_fig)))

    spec_img._restrictSize(17.0 * cm, 8.5 * cm)
    band_img._restrictSize(17.0 * cm, 8.5 * cm)

    elements.append(Paragraph("Tone Balance Reference", styles["Heading3"]))
    elements.append(spec_img)
    elements.append(Spacer(1, 6))

    elements.append(Paragraph("EQ Balance Check", styles["Heading3"]))
    elements.append(band_img)
    elements.append(Spacer(1, 8))

    eq_header = [["Band", "Range", "Avg Dev", "EQ Suggestion"]]
    eq_rows = [[r["Band"], r["Range"], r["AvgDev"], r["EQ"]] for r in results["bands"]]

    eq_tbl = Table(eq_header + eq_rows, hAlign="LEFT", colWidths=[3 * cm, 4 * cm, 3 * cm, 7 * cm])
    eq_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ("ALIGN", (2, 1), (2, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))

    elements.append(Paragraph("Per-band EQ Suggestions", styles["Heading3"]))
    elements.append(eq_tbl)
    elements.append(Spacer(1, 6))

    elements.append(Paragraph("Automated analysis", styles["Small"]))

    doc.build(elements)


class SongAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Song Analyzer")
        self.root.geometry("1050x780")

        self.results = None
        self.spectrum_canvas = None
        self.band_canvas = None

        self.build_ui()

    def build_ui(self):
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill="both", expand=True)

        title = ttk.Label(main, text="Song Analyzer", font=("Segoe UI", 18, "bold"))
        title.pack(anchor="w")

        info_text = "Drag an audio file here or use Select Audio File."
        if not DND_AVAILABLE:
            info_text += " Drag/drop needs: pip install tkinterdnd2"

        self.drop_frame = ttk.LabelFrame(main, text="Input", padding=12)
        self.drop_frame.pack(fill="x", pady=(10, 10))

        self.drop_label = ttk.Label(
            self.drop_frame,
            text=info_text,
            anchor="center",
            font=("Segoe UI", 11)
        )
        self.drop_label.pack(fill="x", ipady=20)

        if DND_AVAILABLE:
            for target in (self.root, self.drop_frame, self.drop_label):
                target.drop_target_register(DND_FILES)
                target.dnd_bind("<<Drop>>", self.on_drop)

        button_row = ttk.Frame(main)
        button_row.pack(fill="x", pady=(0, 10))

        ttk.Button(button_row, text="Select Audio File", command=self.select_file).pack(side="left")
        ttk.Button(button_row, text="Export PDF", command=self.export_pdf).pack(side="left", padx=(8, 0))

        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(button_row, textvariable=self.status_var).pack(side="left", padx=(12, 0))

        content = ttk.Frame(main)
        content.pack(fill="both", expand=True)

        left = ttk.Frame(content)
        left.pack(side="left", fill="both", expand=False)

        right = ttk.Frame(content)
        right.pack(side="left", fill="both", expand=True, padx=(12, 0))

        self.summary = tk.Text(left, width=45, height=36, wrap="word")
        self.summary.pack(fill="both", expand=True)

        self.plot_frame = ttk.Frame(right)
        self.plot_frame.pack(fill="both", expand=True)

    def on_drop(self, event):
        try:
            files = self.root.tk.splitlist(event.data)
            if files:
                self.load_audio_file(files[0])
        except Exception:
            raw = event.data.strip()
            if raw.startswith("{") and raw.endswith("}"):
                raw = raw[1:-1]
            self.load_audio_file(raw)

    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="Select audio file",
            filetypes=[
                ("Audio files", "*.wav *.mp3 *.flac *.m4a *.aac *.ogg"),
                ("All files", "*.*"),
            ]
        )

        if file_path:
            self.load_audio_file(file_path)

    def load_audio_file(self, file_path):
        path = Path(file_path)

        if not path.exists():
            messagebox.showerror("File not found", str(path))
            return

        if path.suffix.lower() not in AUDIO_EXTS:
            messagebox.showerror("Unsupported file", "Please select a WAV, MP3, FLAC, M4A, AAC or OGG file.")
            return

        self.status_var.set("Analyzing...")
        self.summary.delete("1.0", tk.END)
        self.summary.insert(tk.END, f"Analyzing:\n{path}\n\nPlease wait...")

        thread = threading.Thread(target=self.run_analysis_thread, args=(str(path),), daemon=True)
        thread.start()

    def run_analysis_thread(self, file_path):
        try:
            results = analyze_file(file_path)
            self.root.after(0, lambda: self.show_results(results))
        except Exception as e:
            self.root.after(0, lambda: self.show_error(e))

    def show_error(self, error):
        self.status_var.set("Error.")
        messagebox.showerror("Analysis error", str(error))

    def show_results(self, results):
        self.results = results
        self.status_var.set("Analysis complete.")

        self.summary.delete("1.0", tk.END)

        lufs_txt = f"{results['lufs_integrated']} LUFS" if results["lufs_integrated"] is not None else "n/a"
        true_peak_txt = f"{results['true_peak']} dBTP" if results.get("true_peak") is not None else "n/a"
        tempo_txt = f"{results['tempo_bpm']} BPM" if results["tempo_bpm"] else "n/a"
        key_txt = results["key"] if results.get("key") else "n/a"
        key_conf = f"{results['key_confidence']:.3f}" if results.get("key_confidence") is not None else "n/a"

        text = ""
        text += "YOUTUBE CHECK\n"
        text += "==============================\n"
        text += f"{results['youtube_verdict']}\n"
        text += f"{results['youtube_note']}\n"
        text += f"Loudness: {lufs_txt}\n"
        text += f"True Peak: {true_peak_txt}\n\n"

        text += "SUMMARY\n"
        text += "==============================\n"
        text += f"File: {results['file']}\n"
        text += f"Duration: {results['duration_sec']} sec\n"
        text += f"Sample rate: {results['samplerate']} Hz\n"
        text += f"Tempo: {tempo_txt}\n"
        text += f"Estimated key: {key_txt}\n"
        text += f"Key confidence: {key_conf}\n"
        text += f"Tonal tilt: {results['tilt_note']}\n\n"

        text += "EQ NOTES\n"
        text += "==============================\n"
        text += "Positive = too much in that area.\n"
        text += "Negative = too little in that area.\n\n"

        for r in results["bands"]:
            text += f"{r['Band']} ({r['Range']}): {r['AvgDev']} -> {r['EQ']}\n"

        self.summary.insert(tk.END, text)

        self.draw_plots(results)

    def draw_plots(self, results):
        for widget in self.plot_frame.winfo_children():
            widget.destroy()

        spec_fig = build_spectrum_figure(results)
        band_fig = build_band_figure(results)

        spec_canvas = FigureCanvasTkAgg(spec_fig, master=self.plot_frame)
        spec_canvas.draw()
        spec_canvas.get_tk_widget().pack(fill="both", expand=True)

        band_canvas = FigureCanvasTkAgg(band_fig, master=self.plot_frame)
        band_canvas.draw()
        band_canvas.get_tk_widget().pack(fill="both", expand=True)

        self.spectrum_canvas = spec_canvas
        self.band_canvas = band_canvas

    def export_pdf(self):
        if not self.results:
            messagebox.showinfo("No analysis", "Analyze a song first.")
            return

        original = Path(self.results["file_path"])
        default_name = f"{original.stem}_analysis.pdf"

        output_path = filedialog.asksaveasfilename(
            title="Save PDF report",
            defaultextension=".pdf",
            initialdir=str(get_downloads_folder()),
            initialfile=default_name,
            filetypes=[("PDF files", "*.pdf")]
        )

        if not output_path:
            return

        try:
            write_pdf(self.results, Path(output_path))
            messagebox.showinfo("PDF saved", output_path)
        except Exception as e:
            messagebox.showerror("PDF error", str(e))


def main():
    if DND_AVAILABLE:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()

    SongAnalyzerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

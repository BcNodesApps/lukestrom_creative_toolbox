import os
import threading
import tkinter as tk
from tkinter import messagebox
from yt_dlp import YoutubeDL
from yt_dlp.utils import download_range_func


APP_TITLE = "YouTube Video Downloader v6"
FFMPEG_FOLDER = r"C:\ffmpeg\bin"


def get_downloads_folder():
    return os.path.join(os.path.expanduser("~"), "Downloads")


def parse_time_to_seconds(value):
    value = value.strip()

    if not value:
        return None

    if value.isdigit():
        return int(value)

    parts = value.split(":")

    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])

    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])

    raise ValueError("Use seconds, MM:SS, or HH:MM:SS.")


def seconds_to_label(seconds):
    if seconds is None:
        return "end"

    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60

    if h:
        return f"{h:02d}-{m:02d}-{s:02d}"

    return f"{m:02d}-{s:02d}"


def write_status(text):
    root.after(0, lambda: status_text.insert(tk.END, text))
    root.after(0, lambda: status_text.see(tk.END))


class GuiLogger:
    def debug(self, msg):
        if msg.strip():
            write_status(msg + "\n")

    def warning(self, msg):
        write_status("WARNING: " + msg + "\n")

    def error(self, msg):
        write_status("ERROR: " + msg + "\n")


def progress_hook(d):
    if d.get("status") == "downloading":
        percent = d.get("_percent_str", "").strip()
        speed = d.get("_speed_str", "").strip()
        eta = d.get("_eta_str", "").strip()
        write_status(f"Downloading: {percent} | Speed: {speed} | ETA: {eta}\n")

    elif d.get("status") == "finished":
        write_status("Download finished. Processing MP4...\n")


def download_video():
    url = url_entry.get().strip()
    start_raw = start_entry.get().strip()
    end_raw = end_entry.get().strip()

    if not url:
        messagebox.showwarning("Missing link", "Paste a YouTube link first.")
        return

    if not os.path.exists(os.path.join(FFMPEG_FOLDER, "ffmpeg.exe")):
        messagebox.showerror(
            "ffmpeg not found",
            f"ffmpeg.exe not found in:\n\n{FFMPEG_FOLDER}"
        )
        return

    try:
        start_seconds = parse_time_to_seconds(start_raw)
        end_seconds = parse_time_to_seconds(end_raw)

        if start_seconds is not None and end_seconds is not None:
            if end_seconds <= start_seconds:
                messagebox.showwarning("Invalid time range", "End time must be later than start time.")
                return

        if start_seconds is None and end_seconds is not None:
            start_seconds = 0

    except ValueError as e:
        messagebox.showwarning("Invalid time format", str(e))
        return

    downloads_folder = get_downloads_folder()

    clip_label = ""
    if start_seconds is not None or end_seconds is not None:
        clip_label = f" - clip {seconds_to_label(start_seconds)} to {seconds_to_label(end_seconds)}"

    output_template = os.path.join(
        downloads_folder,
        f"%(title).200B - %(resolution)s{clip_label}.%(ext)s"
    )

    ydl_opts = {
        "format": "bestvideo[ext=mp4]/bestvideo",
        "outtmpl": output_template,
        "noplaylist": True,
        "remuxvideo": "mp4",
        "ffmpeg_location": FFMPEG_FOLDER,
        "logger": GuiLogger(),
        "progress_hooks": [progress_hook],
    }

    if start_seconds is not None or end_seconds is not None:
        ydl_opts["download_ranges"] = download_range_func(
            None,
            [(start_seconds, end_seconds)]
        )
        ydl_opts["force_keyframes_at_cuts"] = True

    download_button.config(state="disabled")
    status_text.delete("1.0", tk.END)

    if start_seconds is None and end_seconds is None:
        write_status("Mode: full video\n\n")
    else:
        write_status(f"Mode: clip {start_raw or '00:00'} to {end_raw or 'end'}\n\n")

    def run():
        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            write_status("\nDone.\n")
            write_status(f"Saved in: {downloads_folder}\n")

        except Exception as e:
            write_status(f"\nError: {e}\n")

        finally:
            root.after(0, lambda: download_button.config(state="normal"))

    threading.Thread(target=run, daemon=True).start()


root = tk.Tk()
root.title(APP_TITLE)
root.geometry("780x500")
root.resizable(False, False)

tk.Label(root, text=APP_TITLE, font=("Segoe UI", 16, "bold")).pack(pady=(15, 5))

tk.Label(
    root,
    text="Paste a YouTube link. Leave start/end empty to download the full video.",
    font=("Segoe UI", 9),
    wraplength=710
).pack(pady=(0, 15))

url_entry = tk.Entry(root, font=("Segoe UI", 11), width=88)
url_entry.pack(pady=5)

time_frame = tk.Frame(root)
time_frame.pack(pady=8)

tk.Label(time_frame, text="Start time:", font=("Segoe UI", 10)).pack(side="left", padx=(0, 5))
start_entry = tk.Entry(time_frame, font=("Segoe UI", 10), width=15)
start_entry.pack(side="left", padx=(0, 20))

tk.Label(time_frame, text="End time:", font=("Segoe UI", 10)).pack(side="left", padx=(0, 5))
end_entry = tk.Entry(time_frame, font=("Segoe UI", 10), width=15)
end_entry.pack(side="left")

tk.Label(
    root,
    text="Time format: seconds, MM:SS, or HH:MM:SS. Example: 90, 01:30, 00:01:30",
    font=("Segoe UI", 8)
).pack(pady=(0, 8))

download_button = tk.Button(
    root,
    text="Download highest quality MP4 without sound",
    font=("Segoe UI", 10, "bold"),
    command=download_video
)
download_button.pack(pady=8)

status_text = tk.Text(root, height=15, width=92, font=("Consolas", 9))
status_text.pack(pady=10)

root.mainloop()
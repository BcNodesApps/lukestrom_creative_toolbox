import os
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import messagebox


APP_TITLE = "YouTube Video Downloader v3"
FFMPEG_FOLDER = r"C:\ffmpeg\bin"


def get_downloads_folder():
    return os.path.join(os.path.expanduser("~"), "Downloads")


def parse_time(value):
    value = value.strip()

    if not value:
        return ""

    if value.isdigit():
        seconds = int(value)
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

    parts = value.split(":")

    if len(parts) == 2:
        m, s = parts
        return f"00:{int(m):02d}:{int(s):02d}"

    if len(parts) == 3:
        h, m, s = parts
        return f"{int(h):02d}:{int(m):02d}:{int(s):02d}"

    raise ValueError("Use seconds, MM:SS, or HH:MM:SS.")


def safe_time_label(time_value):
    if not time_value:
        return "end"
    return time_value.replace(":", "-")


def write_status(text):
    root.after(0, lambda: status_text.insert(tk.END, text))
    root.after(0, lambda: status_text.see(tk.END))


def download_video():
    url = url_entry.get().strip()
    start_raw = start_entry.get().strip()
    end_raw = end_entry.get().strip()

    if not url:
        messagebox.showwarning("Missing link", "Paste a YouTube link first.")
        return

    if not os.path.exists(os.path.join(FFMPEG_FOLDER, "ffmpeg.exe")):
        messagebox.showerror("ffmpeg not found", f"ffmpeg.exe not found in:\n\n{FFMPEG_FOLDER}")
        return

    if shutil.which("yt-dlp") is None:
        messagebox.showerror("yt-dlp not found", "yt-dlp is not available in PATH.")
        return

    try:
        start_time = parse_time(start_raw)
        end_time = parse_time(end_raw)

        if start_time and end_time and end_time <= start_time:
            messagebox.showwarning("Invalid time range", "End time must be later than start time.")
            return

        if not start_time and end_time:
            start_time = "00:00:00"

    except ValueError as e:
        messagebox.showwarning("Invalid time format", str(e))
        return

    downloads_folder = get_downloads_folder()

    if start_time or end_time:
        clip_label = f" - clip {safe_time_label(start_time)} to {safe_time_label(end_time)}"
    else:
        clip_label = ""

    output_template = os.path.join(
        downloads_folder,
        f"%(title).200B - %(resolution)s{clip_label}.%(ext)s"
    )

    cmd = [
        "yt-dlp",
        "--ffmpeg-location", FFMPEG_FOLDER,
        "-f", "bestvideo[ext=mp4]/bestvideo",
        "--remux-video", "mp4",
        "--no-playlist",
        "-o", output_template,
    ]

    if start_time or end_time:
        section = f"*{start_time}-{end_time}"
        cmd.extend(["--download-sections", section])

    cmd.append(url)

    download_button.config(state="disabled")
    status_text.delete("1.0", tk.END)

    if start_time or end_time:
        write_status(f"Mode: clip {start_time or 'start'} to {end_time or 'end'}\n\n")
    else:
        write_status("Mode: full video\n\n")

    def run():
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace"
            )

            for line in process.stdout:
                write_status(line)

            process.wait()

            if process.returncode == 0:
                write_status("\nDone.\n")
                write_status(f"Saved in: {downloads_folder}\n")
            else:
                write_status("\nDownload failed.\n")

        except Exception as e:
            write_status(f"\nError: {e}\n")

        finally:
            root.after(0, lambda: download_button.config(state="normal"))

    threading.Thread(target=run, daemon=True).start()


root = tk.Tk()
root.title(APP_TITLE)
root.geometry("780x500")
root.resizable(False, False)

title_label = tk.Label(root, text=APP_TITLE, font=("Segoe UI", 16, "bold"))
title_label.pack(pady=(15, 5))

info_label = tk.Label(
    root,
    text="Paste a YouTube link. Leave start/end empty to download the full video.",
    font=("Segoe UI", 9),
    wraplength=710
)
info_label.pack(pady=(0, 15))

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

hint_label = tk.Label(
    root,
    text="Time format: seconds, MM:SS, or HH:MM:SS. Example: 90, 01:30, 00:01:30",
    font=("Segoe UI", 8)
)
hint_label.pack(pady=(0, 8))

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
import os
import threading
import tkinter as tk
from tkinter import messagebox

import yt_dlp
from yt_dlp import YoutubeDL


APP_TITLE = "YouTube Video Downloader v3"

FFMPEG_PATH = r"C:\ffmpeg\bin"
RELEASE_NOTES_FILE = r"C:\appdevelopment\toolbox\8-youtube_dl\release notes.txt"


def get_downloads_folder():
    return os.path.join(os.path.expanduser("~"), "Downloads")


def write_status(text):
    root.after(0, lambda: status_text.insert(tk.END, text))
    root.after(0, lambda: status_text.see(tk.END))


def show_release_notes():
    try:
        with open(RELEASE_NOTES_FILE, "r", encoding="utf-8") as file:
            content = file.read()
    except FileNotFoundError:
        content = "Release notes file not found."

    notes_window = tk.Toplevel(root)
    notes_window.title("Release Notes")
    notes_window.geometry("700x500")

    notes_text = tk.Text(
        notes_window,
        wrap="word",
        font=("Segoe UI", 10)
    )
    notes_text.pack(fill="both", expand=True, padx=10, pady=10)
    notes_text.insert("1.0", content)
    notes_text.config(state="disabled")


class GuiLogger:
    def debug(self, msg):
        if msg:
            write_status(str(msg) + "\n")

    def warning(self, msg):
        write_status("WARNING: " + str(msg) + "\n")

    def error(self, msg):
        write_status("ERROR: " + str(msg) + "\n")


def progress_hook(d):
    if d.get("status") == "downloading":
        percent = d.get("_percent_str", "").strip()
        speed = d.get("_speed_str", "").strip()
        eta = d.get("_eta_str", "").strip()

        write_status(
            f"Downloading: {percent} | Speed: {speed} | ETA: {eta}\n"
        )

    elif d.get("status") == "finished":
        write_status("Download finished. Processing MP4...\n")


def download_video():
    url = url_entry.get().strip()

    if not url:
        messagebox.showwarning("Missing link", "Paste a YouTube link first.")
        return

    downloads_folder = get_downloads_folder()

    output_template = os.path.join(
        downloads_folder,
        "%(title).200B - %(resolution)s.%(ext)s"
    )

    ydl_opts = {
        "format": "bestvideo+bestaudio/best",
        "outtmpl": output_template,
        "noplaylist": True,
        "remuxvideo": "mp4",
        "merge_output_format": "mp4",
        "ffmpeg_location": FFMPEG_PATH,
        "logger": GuiLogger(),
        "progress_hooks": [progress_hook],
    }

    download_button.config(state="disabled")
    status_text.delete("1.0", tk.END)
    write_status("Starting download...\n\n")

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
root.geometry("760x470")
root.resizable(False, False)

title_label = tk.Label(
    root,
    text=APP_TITLE,
    font=("Segoe UI", 16, "bold")
)
title_label.pack(pady=(15, 5))

info_label = tk.Label(
    root,
    text="Paste a YouTube link. The app downloads the highest available video with sound and saves it as MP4 in Downloads.",
    font=("Segoe UI", 9),
    wraplength=690
)
info_label.pack(pady=(0, 15))

url_entry = tk.Entry(
    root,
    font=("Segoe UI", 11),
    width=85
)
url_entry.pack(pady=5)

button_frame = tk.Frame(root)
button_frame.pack(pady=10)

download_button = tk.Button(
    button_frame,
    text="Download",
    font=("Segoe UI", 10, "bold"),
    command=download_video
)
download_button.pack(side="left", padx=10)

release_notes_button = tk.Button(
    button_frame,
    text="Release notes",
    font=("Segoe UI", 10),
    command=show_release_notes
)
release_notes_button.pack(side="left", padx=10)

status_text = tk.Text(
    root,
    height=15,
    width=90,
    font=("Consolas", 9)
)
status_text.pack(pady=10)

root.mainloop()
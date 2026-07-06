import os
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import messagebox


APP_TITLE = "YouTube Video Downloader v1"


def get_downloads_folder():
    return os.path.join(os.path.expanduser("~"), "Downloads")


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

    cmd = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--no-playlist",
        "-f",
        "bestvideo",
        "--remux-video",
        "mp4",
        "-o",
        output_template,
        url,
    ]

    download_button.config(state="disabled")
    status_text.delete("1.0", tk.END)
    status_text.insert(tk.END, "Starting download...\n\n")

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
                status_text.insert(tk.END, line)
                status_text.see(tk.END)

            process.wait()

            if process.returncode == 0:
                status_text.insert(tk.END, "\nDone.\n")
                status_text.insert(tk.END, f"Saved in: {downloads_folder}\n")
            else:
                status_text.insert(tk.END, "\nDownload failed.\n")

        except Exception as e:
            status_text.insert(tk.END, f"\nError: {e}\n")

        finally:
            download_button.config(state="normal")

    threading.Thread(target=run, daemon=True).start()


root = tk.Tk()
root.title(APP_TITLE)
root.geometry("720x420")
root.resizable(False, False)

title_label = tk.Label(root, text=APP_TITLE, font=("Segoe UI", 16, "bold"))
title_label.pack(pady=(15, 5))

info_label = tk.Label(
    root,
    text="Paste a YouTube link. The app downloads the highest available video-only stream and saves it as MP4 in Downloads.",
    font=("Segoe UI", 9),
    wraplength=650
)
info_label.pack(pady=(0, 15))

url_entry = tk.Entry(root, font=("Segoe UI", 11), width=80)
url_entry.pack(pady=5)

download_button = tk.Button(
    root,
    text="Download highest quality MP4 without sound",
    font=("Segoe UI", 10, "bold"),
    command=download_video
)
download_button.pack(pady=10)

status_text = tk.Text(root, height=14, width=85, font=("Consolas", 9))
status_text.pack(pady=10)

root.mainloop()
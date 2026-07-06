import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date, time, timedelta
from pathlib import Path
import random
from tkcalendar import DateEntry
import uuid


DOWNLOADS_PATH = Path.home() / "Downloads"

URL_TIKTOK = "https://www.tiktok.com/tiktokstudio/upload?from=webapp&lang=en-GB"
URL_YOUTUBE = "https://studio.youtube.com/channel/UCAUCC7uw_shkAmX7kPMy5IQ/videos/upload?d=ud&filter=%5B%5D&sort=%7B%22columnType%22%3A%22date%22%2C%22sortOrder%22%3A%22DESCENDING%22%7D"
URL_INSTAGRAM = "https://www.instagram.com/lukestrommusic/"
URL_FACEBOOK = "https://www.facebook.com/lukestrommusic/reels/"
URL_DISTROKID = "https://distrokid.com/new/"


def safe_song_title(title: str) -> str:
    return " ".join(title.strip().split()).lower()


def generate_output_name(title: str, start_date: datetime) -> str:
    safe_title = safe_song_title(title)
    date_prefix = start_date.strftime("%y%m%d")
    return f"{date_prefix}_{safe_title}_schedule.ics"


def dated_video_filename(date_prefix: str, song_title: str, label: str, resolution: str) -> str:
    return f"{date_prefix} {song_title} {label} {resolution}"


def grouped_cover_filename(date_prefix: str, platforms: str, song_title: str, label: str, resolution: str) -> str:
    return f"{date_prefix} {platforms} {song_title} {label} {resolution}"


def single_platform_filename(date_prefix: str, platform: str, song_title: str, label: str, resolution: str) -> str:
    return f"{date_prefix} {platform} {song_title} {label} {resolution}"


def get_random_event_time() -> time:
    hour = random.randint(10, 22)
    minute = random.choice([0, 15, 30, 45])
    return time(hour, minute)


def add_task(schedule: list, task_date: date, song_title: str, clean_title: str, date_prefix: str, task_key: str):
    schedule.append({
        "datetime": datetime.combine(task_date, get_random_event_time()),
        "task": f"{task_key} for {song_title}",
        "description": build_description(clean_title, date_prefix, task_key),
    })


def build_schedule(
    song_title: str,
    start_date: date,
    song_type: str,
    reels_days_after_full_video: int,
    initial_post_1_days_after_reels: int,
    initial_post_2_days_after_post_1: int,
    repost_1_days_after_post_2: int,
    repost_2_days_after_repost_1: int
):
    schedule = []
    clean_title = safe_song_title(song_title)
    date_prefix = start_date.strftime("%y%m%d")

    current_date = start_date

    add_task(schedule, current_date, song_title, clean_title, date_prefix, "create full video")

    current_date = current_date + timedelta(days=max(1, reels_days_after_full_video))
    add_task(schedule, current_date, song_title, clean_title, date_prefix, "create reels")

    current_date = current_date + timedelta(days=1)
    add_task(schedule, current_date, song_title, clean_title, date_prefix, "create thumbnail and covers")

    if song_type == "new":
        current_date = current_date + timedelta(days=1)
        add_task(schedule, current_date, song_title, clean_title, date_prefix, "upload to DistroKid")

    current_date = current_date + timedelta(days=max(1, initial_post_1_days_after_reels))
    add_task(schedule, current_date, song_title, clean_title, date_prefix, "publish reel 1")

    if song_type == "new":
        current_date = current_date + timedelta(days=max(1, initial_post_2_days_after_post_1))
        add_task(schedule, current_date, song_title, clean_title, date_prefix, "publish reel 2")

        current_date = current_date + timedelta(days=max(1, repost_1_days_after_post_2))
        add_task(schedule, current_date, song_title, clean_title, date_prefix, "repost reel 1")

        current_date = current_date + timedelta(days=max(1, repost_2_days_after_repost_1))
        add_task(schedule, current_date, song_title, clean_title, date_prefix, "repost reel 2")
    else:
        current_date = current_date + timedelta(days=max(1, repost_1_days_after_post_2))
        add_task(schedule, current_date, song_title, clean_title, date_prefix, "repost reel 1")

    current_date = current_date + timedelta(days=23)
    add_task(schedule, current_date, song_title, clean_title, date_prefix, "review and cleanup")

    return schedule


def build_description(song_title: str, date_prefix: str, task_name: str) -> str:
    lines = []

    lines.extend(get_filenames_for_task(song_title, date_prefix, task_name))

    lines.append("")
    lines.append("ChatGPT prompt:")
    lines.append(get_prompt_for_task(song_title, task_name))

    urls = get_urls_for_task(task_name)
    if urls:
        lines.append("")
        lines.append("URLs:")
        lines.extend(urls)

    return "\n".join(lines)


def get_filenames_for_task(song_title: str, date_prefix: str, task_name: str):
    if task_name == "create full video":
        return [
            "to create",
            dated_video_filename(date_prefix, song_title, "full", "3840x2160"),
        ]

    if task_name == "create reels":
        return [
            "to create",
            dated_video_filename(date_prefix, song_title, "1 initial", "1080x1920"),
            dated_video_filename(date_prefix, song_title, "1 repost", "1080x1920"),
            dated_video_filename(date_prefix, song_title, "2 initial", "1080x1920"),
            dated_video_filename(date_prefix, song_title, "2 repost", "1080x1920"),
        ]

    if task_name == "create thumbnail and covers":
        return [
            "to create",
            single_platform_filename(date_prefix, "yt", song_title, "cover", "1280x720"),
            grouped_cover_filename(date_prefix, "tt yt ig fb", song_title, "1 initial cover", "1080x1920"),
            grouped_cover_filename(date_prefix, "tt yt ig fb", song_title, "1 repost cover", "1080x1920"),
            grouped_cover_filename(date_prefix, "tt yt ig fb", song_title, "2 initial cover", "1080x1920"),
            grouped_cover_filename(date_prefix, "tt yt ig fb", song_title, "2 repost cover", "1080x1920"),
            single_platform_filename(date_prefix, "dk", song_title, "cover", "3000x3000"),
        ]

    if task_name == "upload to DistroKid":
        return [
            "to create",
            single_platform_filename(date_prefix, "dk", song_title, "cover", "3000x3000"),
        ]

    if task_name == "publish reel 1":
        return [
            "to create",
            dated_video_filename(date_prefix, song_title, "1 initial", "1080x1920"),
            grouped_cover_filename(date_prefix, "tt yt ig fb", song_title, "1 initial cover", "1080x1920"),
        ]

    if task_name == "repost reel 1":
        return [
            "to create",
            dated_video_filename(date_prefix, song_title, "1 repost", "1080x1920"),
            grouped_cover_filename(date_prefix, "tt yt ig fb", song_title, "1 repost cover", "1080x1920"),
        ]

    if task_name == "publish reel 2":
        return [
            "to create",
            dated_video_filename(date_prefix, song_title, "2 initial", "1080x1920"),
            grouped_cover_filename(date_prefix, "tt yt ig fb", song_title, "2 initial cover", "1080x1920"),
        ]

    if task_name == "repost reel 2":
        return [
            "to create",
            dated_video_filename(date_prefix, song_title, "2 repost", "1080x1920"),
            grouped_cover_filename(date_prefix, "tt yt ig fb", song_title, "2 repost cover", "1080x1920"),
        ]

    return [
        "to create",
        f"{date_prefix} {song_title} archive folder"
    ]


def get_prompt_for_task(song_title: str, task_name: str):
    if task_name == "create full video":
        return (
            f"Generate a concise production checklist for creating the full video for '{song_title}'. "
            f"Keep it practical and action-oriented."
        )

    if task_name == "create reels":
        return (
            f"Generate a concise production checklist for creating 4 reel versions for '{song_title}': "
            f"1 initial, 1 repost, 2 initial, 2 repost. "
            f"Keep it practical and action-oriented."
        )

    if task_name == "upload to DistroKid":
        return (
            f"Generate DistroKid release text for '{song_title}'. "
            f"Separate title and description if needed. No hashtags."
        )

    return (
        f"Generate platform-specific (tt, yt, ig, fb) caption + hashtags for '{song_title}' "
        f"for task '{task_name}'. Separate title and description if needed. "
        f"Keep it in Lukestrom style. Make each post stand alone. Do not make it feel generic."
    )


def get_urls_for_task(task_name: str):
    if task_name == "upload to DistroKid":
        return [URL_DISTROKID]

    if task_name in ["publish reel 1", "publish reel 2", "repost reel 1", "repost reel 2"]:
        return [
            URL_TIKTOK,
            URL_YOUTUBE,
            URL_INSTAGRAM,
            URL_FACEBOOK,
        ]

    return []


def format_ics_datetime(dt: datetime) -> str:
    return dt.strftime("%Y%m%dT%H%M%S")


def create_ics_content(schedule: list[dict]) -> str:
    now_stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Lukestrom//4-Post Planner//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]

    for item in schedule:
        start_dt = item["datetime"]
        end_dt = start_dt + timedelta(minutes=30)
        description = item["description"].replace("\n", "\\n")
        uid = f"{uuid.uuid4()}@lukestrom.local"

        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{now_stamp}",
            f"DTSTART:{format_ics_datetime(start_dt)}",
            f"DTEND:{format_ics_datetime(end_dt)}",
            f"SUMMARY:{item['task']}",
            f"DESCRIPTION:{description}",
            "END:VEVENT",
        ])

    lines.append("END:VCALENDAR")
    return "\n".join(lines)


def run_app():
    title = title_var.get().strip()
    song_type = type_var.get().strip().lower()

    if not title:
        messagebox.showerror("Error", "Please enter a song title.")
        return

    try:
        reels_days_after_full_video = int(reels_days_after_full_video_var.get())
        initial_post_1_days_after_reels = int(initial_post_1_days_after_reels_var.get())
        initial_post_2_days_after_post_1 = int(initial_post_2_days_after_post_1_var.get())
        repost_1_days_after_post_2 = int(repost_1_days_after_post_2_var.get())
        repost_2_days_after_repost_1 = int(repost_2_days_after_repost_1_var.get())
    except ValueError:
        messagebox.showerror("Error", "Intervals must be whole numbers.")
        return

    start_date = date_entry.get_date()
    start_date_dt = datetime.combine(start_date, datetime.min.time())

    output_name = generate_output_name(title, start_date_dt)
    output_path = DOWNLOADS_PATH / output_name

    schedule = build_schedule(
        title,
        start_date,
        song_type,
        reels_days_after_full_video,
        initial_post_1_days_after_reels,
        initial_post_2_days_after_post_1,
        repost_1_days_after_post_2,
        repost_2_days_after_repost_1,
    )

    ics_content = create_ics_content(schedule)
    output_path.write_text(ics_content, encoding="utf-8")

    lines = [
        f"Title: {title}",
        f"Start date: {start_date_dt.strftime('%Y-%m-%d')}",
        f"Type: {song_type}",
        f"Output file: {output_path}",
        "",
        "Schedule details:",
        ""
    ]

    for item in schedule:
        lines.append("=" * 70)
        lines.append(f"{item['datetime'].strftime('%Y-%m-%d %H:%M')}  {item['task']}")
        lines.append("")
        lines.append(item["description"])
        lines.append("")

    result_box.delete("1.0", tk.END)
    result_box.insert(tk.END, "\n".join(lines))
    messagebox.showinfo("Done", f"ICS file created:\n{output_path}")


def apply_type_defaults():
    reels_days_after_full_video_var.set("1")
    initial_post_1_days_after_reels_var.set("1")

    if type_var.get() == "new":
        initial_post_2_days_after_post_1_var.set("1")
        repost_1_days_after_post_2_var.set("7")
        repost_2_days_after_repost_1_var.set("1")

        initial_post_2_days_after_post_1_entry.configure(state="normal")
        repost_1_days_after_post_2_entry.configure(state="normal")
        repost_2_days_after_repost_1_entry.configure(state="normal")

        initial_post_2_days_after_post_1_label.configure(text="Days from publish reel 1 to publish reel 2")
        repost_1_days_after_post_2_label.configure(text="Days from publish reel 2 to repost reel 1")
        repost_2_days_after_repost_1_label.configure(text="Days from repost reel 1 to repost reel 2")
    else:
        initial_post_2_days_after_post_1_var.set("0")
        repost_1_days_after_post_2_var.set("7")
        repost_2_days_after_repost_1_var.set("0")

        initial_post_2_days_after_post_1_entry.configure(state="disabled")
        repost_1_days_after_post_2_entry.configure(state="normal")
        repost_2_days_after_repost_1_entry.configure(state="disabled")

        initial_post_2_days_after_post_1_label.configure(text="Not used for vintage")
        repost_1_days_after_post_2_label.configure(text="Days from publish reel 1 to repost reel 1")
        repost_2_days_after_repost_1_label.configure(text="Not used for vintage")


root = tk.Tk()
root.title("4-Post Planner")
root.geometry("980x840")
root.resizable(False, False)

main_frame = ttk.Frame(root, padding=20)
main_frame.pack(fill="both", expand=True)

title_var = tk.StringVar()
type_var = tk.StringVar(value="new")

reels_days_after_full_video_var = tk.StringVar(value="1")
initial_post_1_days_after_reels_var = tk.StringVar(value="1")
initial_post_2_days_after_post_1_var = tk.StringVar(value="1")
repost_1_days_after_post_2_var = tk.StringVar(value="7")
repost_2_days_after_repost_1_var = tk.StringVar(value="1")

ttk.Label(main_frame, text="Song title").grid(row=0, column=0, sticky="w", pady=(0, 5))
ttk.Entry(main_frame, width=40, textvariable=title_var).grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 10))

ttk.Label(main_frame, text="Start date").grid(row=2, column=0, sticky="w", pady=(0, 5))
date_entry = DateEntry(main_frame, width=18, date_pattern="yyyy-mm-dd")
date_entry.grid(row=3, column=0, sticky="w", pady=(0, 10))

ttk.Label(main_frame, text="Type").grid(row=4, column=0, sticky="w", pady=(0, 5))
type_frame = ttk.Frame(main_frame)
type_frame.grid(row=5, column=0, sticky="w", pady=(0, 10))
ttk.Radiobutton(type_frame, text="New", variable=type_var, value="new", command=apply_type_defaults).pack(side="left", padx=(0, 10))
ttk.Radiobutton(type_frame, text="Vintage", variable=type_var, value="vintage", command=apply_type_defaults).pack(side="left")

ttk.Label(main_frame, text="Days from full video to reels").grid(row=6, column=0, sticky="w")
ttk.Entry(main_frame, width=10, textvariable=reels_days_after_full_video_var).grid(row=7, column=0, sticky="w", pady=(0, 8))

ttk.Label(main_frame, text="Days from reels to publish reel 1").grid(row=8, column=0, sticky="w")
ttk.Entry(main_frame, width=10, textvariable=initial_post_1_days_after_reels_var).grid(row=9, column=0, sticky="w", pady=(0, 8))

initial_post_2_days_after_post_1_label = ttk.Label(main_frame, text="Days from publish reel 1 to publish reel 2")
initial_post_2_days_after_post_1_label.grid(row=10, column=0, sticky="w")
initial_post_2_days_after_post_1_entry = ttk.Entry(main_frame, width=10, textvariable=initial_post_2_days_after_post_1_var)
initial_post_2_days_after_post_1_entry.grid(row=11, column=0, sticky="w", pady=(0, 8))

repost_1_days_after_post_2_label = ttk.Label(main_frame, text="Days from publish reel 2 to repost reel 1")
repost_1_days_after_post_2_label.grid(row=12, column=0, sticky="w")
repost_1_days_after_post_2_entry = ttk.Entry(main_frame, width=10, textvariable=repost_1_days_after_post_2_var)
repost_1_days_after_post_2_entry.grid(row=13, column=0, sticky="w", pady=(0, 8))

repost_2_days_after_repost_1_label = ttk.Label(main_frame, text="Days from repost reel 1 to repost reel 2")
repost_2_days_after_repost_1_label.grid(row=14, column=0, sticky="w")
repost_2_days_after_repost_1_entry = ttk.Entry(main_frame, width=10, textvariable=repost_2_days_after_repost_1_var)
repost_2_days_after_repost_1_entry.grid(row=15, column=0, sticky="w", pady=(0, 12))

ttk.Button(main_frame, text="Generate", command=run_app).grid(row=16, column=0, sticky="w", pady=(0, 15))

ttk.Label(main_frame, text="Result").grid(row=17, column=0, sticky="w")

result_box = tk.Text(main_frame, width=110, height=30, wrap="word")
result_box.grid(row=18, column=0, columnspan=3, sticky="nsew")

scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=result_box.yview)
scrollbar.grid(row=18, column=3, sticky="ns")
result_box.configure(yscrollcommand=scrollbar.set)

apply_type_defaults()
root.mainloop()
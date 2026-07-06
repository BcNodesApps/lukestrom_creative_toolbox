import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date, time, timedelta
from pathlib import Path
import uuid
import webbrowser


DOWNLOADS_PATH = Path.home() / "Downloads"

URL_DISTROKID = "https://distrokid.com/mymusic/"
URL_YOUTUBE = "https://studio.youtube.com/channel/UCAUCC7uw_shkAmX7kPMy5IQ/videos/upload?d=ud&filter=%5B%5D&sort=%7B%22columnType%22%3A%22date%22%2C%22sortOrder%22%3A%22DESCENDING%22%7D"
URL_FACEBOOK = "https://business.facebook.com/latest/posts/published_posts/?business_id=678482264451473&asset_id=1126335547219736"
URL_TIKTOK = "https://www.tiktok.com/tiktokstudio/content"

POST_TIME_TEXT = "20:00 Amsterdam time"


def format_ics_datetime(dt: datetime) -> str:
    return dt.strftime("%Y%m%dT%H%M%S")


def safe_filename(text: str) -> str:
    return "_".join(text.strip().lower().split())


def display_song_filename(text: str) -> str:
    return " ".join(text.strip().split())


def clean_multiline(text: str) -> str:
    return text.strip() if text.strip() else "-"


def create_ics(events: list[dict]) -> str:
    now_stamp = datetime.now().strftime("%Y%m%dT%H%M%S")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Lukestrom//Post Planner//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]

    for event in events:
        start_dt = event["datetime"]
        end_dt = start_dt + timedelta(minutes=30)
        description = event["description"].replace("\n", "\\n")

        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{uuid.uuid4()}@lukestrom.local",
            f"DTSTAMP:{now_stamp}",
            f"DTSTART:{format_ics_datetime(start_dt)}",
            f"DTEND:{format_ics_datetime(end_dt)}",
            f"SUMMARY:{event['title']}",
            f"DESCRIPTION:{description}",
            "END:VEVENT",
        ])

    lines.append("END:VCALENDAR")
    return "\n".join(lines)


def get_week_offsets() -> list[int]:
    values = [
        repost1_offset_var.get().strip(),
        repost2_offset_var.get().strip(),
        repost3_offset_var.get().strip(),
        repost4_offset_var.get().strip(),
        repost5_offset_var.get().strip(),
        repost6_offset_var.get().strip(),
    ]

    offsets = []

    for value in values:
        try:
            parsed = int(value)
        except ValueError:
            raise ValueError("Repost intervals must be whole numbers.")

        if parsed < 1:
            raise ValueError("Repost intervals must be 1 week or higher.")

        offsets.append(parsed)

    return offsets


def build_post_schedule_text(song_title: str, post_items: list[dict]) -> str:
    caption = f"Lukestrom - {song_title}"

    lines = [
        song_title.upper(),
        "",
        "POST SCHEDULE",
        "",
        f"Caption/title for all posts: {caption}",
        f"Time for all posts: {POST_TIME_TEXT}",
        "",
        "Platform priority:",
        "1. YouTube Shorts",
        "2. Facebook Reels",
        "3. Instagram Reels",
        "4. TikTok",
        "",
        "URLs:",
        f"DistroKid: {URL_DISTROKID}",
        f"YouTube Shorts: {URL_YOUTUBE}",
        f"Facebook Reels: {URL_FACEBOOK}",
        f"TikTok: {URL_TIKTOK}",
        "",
        "General instructions:",
        "- Upload the listed video file.",
        "- Use the caption/title shown above.",
        "- The first 2 seconds and opening text are already baked into the video.",
        "- Do not create a separate cover.",
        "- Schedule all posts in one session.",
        "",
        "=" * 70,
        "",
    ]

    for item in post_items:
        lines.extend([
            item["label"].upper(),
            f"Date: {item['date'].strftime('%Y-%m-%d')}",
            f"Time: {POST_TIME_TEXT}",
            f"Filename: {item['filename']}",
            f"Caption/title: {caption}",
            "",
            "=" * 70,
            "",
        ])

    return "\n".join(lines)


def build_reel_design_text(song_title: str, post_items: list[dict]) -> str:
    lines = [
        song_title.upper(),
        "",
        "REEL DESIGN",
        "",
        "This file captures the creative decisions for each reel variation.",
        "The scheduling file stays operational; this file stores the creative plan.",
        "",
        "=" * 70,
        "",
    ]

    for item in post_items:
        lines.extend([
            item["label"].upper(),
            "",
            "Filename:",
            item["filename"],
            "",
            "First 2 seconds:",
            clean_multiline(item["first_seconds"]),
            "",
            "Opening text:",
            clean_multiline(item["opening_text"]),
            "",
            "=" * 70,
            "",
        ])

    return "\n".join(lines)


def build_events(song_title: str, schedule_txt_filename: str, design_txt_filename: str) -> list[dict]:
    today = date.today()

    return [
        {
            "datetime": datetime.combine(today + timedelta(days=1), time(20, 0)),
            "title": f"{song_title} - Publish on DistroKid",
            "description": (
                f"Song: {song_title}\n"
                f"Task: Publish on DistroKid\n\n"
                f"Upload the song to DistroKid.\n"
                f"Check title, artist name, credits, lyrics, artwork, and AI/vocal disclosure settings.\n\n"
                f"URL:\n{URL_DISTROKID}"
            ),
        },
        {
            "datetime": datetime.combine(today + timedelta(days=2), time(20, 0)),
            "title": f"{song_title} - Schedule all posts",
            "description": (
                f"Song: {song_title}\n"
                f"Task: Schedule all posts\n\n"
                f"Open the accompanying schedule file:\n"
                f"{schedule_txt_filename}\n\n"
                f"Creative reference file:\n"
                f"{design_txt_filename}\n\n"
                f"Schedule all listed posts at 20:00 Amsterdam time.\n\n"
                f"YouTube: {URL_YOUTUBE}\n"
                f"Facebook: {URL_FACEBOOK}\n"
                f"TikTok: {URL_TIKTOK}"
            ),
        },
        {
            "datetime": datetime.combine(today + timedelta(days=3), time(20, 0)),
            "title": f"{song_title} - Cleanup",
            "description": (
                f"Song: {song_title}\n"
                f"Task: Cleanup\n\n"
                f"- Verify all scheduled posts were created.\n"
                f"- Check the schedule file again if needed: {schedule_txt_filename}\n"
                f"- Store the creative reel design file: {design_txt_filename}\n"
                f"- Archive project files clearly.\n"
                f"- Remove temporary reel files if no longer needed."
            ),
        },
    ]


def generate():
    song_title = song_title_var.get().strip()

    if not song_title:
        messagebox.showerror("Error", "Enter a song title.")
        return

    try:
        week_offsets = get_week_offsets()
    except ValueError as error:
        messagebox.showerror("Error", str(error))
        return

    today = date.today()
    initial_post_date = today + timedelta(days=2)
    filename_song = display_song_filename(song_title)

    post_items = [
        {
            "label": "Initial post",
            "date": initial_post_date,
            "filename": f"initial - {filename_song}.mp4",
            "first_seconds": initial_first_seconds_box.get("1.0", tk.END).strip(),
            "opening_text": initial_opening_text_box.get("1.0", tk.END).strip(),
        }
    ]

    repost_boxes = [
        (repost1_first_seconds_box, repost1_opening_text_box),
        (repost2_first_seconds_box, repost2_opening_text_box),
        (repost3_first_seconds_box, repost3_opening_text_box),
        (repost4_first_seconds_box, repost4_opening_text_box),
        (repost5_first_seconds_box, repost5_opening_text_box),
        (repost6_first_seconds_box, repost6_opening_text_box),
    ]

    for index, weeks in enumerate(week_offsets, start=1):
        first_seconds_box, opening_text_box = repost_boxes[index - 1]

        post_items.append({
            "label": f"Repost {index} (+{weeks} weeks)",
            "date": initial_post_date + timedelta(weeks=weeks),
            "filename": f"repost {index} - {filename_song}.mp4",
            "first_seconds": first_seconds_box.get("1.0", tk.END).strip(),
            "opening_text": opening_text_box.get("1.0", tk.END).strip(),
        })

    date_prefix = today.strftime("%y%m%d")
    safe_title = safe_filename(song_title)

    ics_filename = f"{date_prefix}_{safe_title}_catalog.ics"
    schedule_txt_filename = f"{date_prefix}_{safe_title}_post_schedule.txt"
    design_txt_filename = f"{date_prefix}_{safe_title}_reel_design.txt"

    ics_path = DOWNLOADS_PATH / ics_filename
    schedule_txt_path = DOWNLOADS_PATH / schedule_txt_filename
    design_txt_path = DOWNLOADS_PATH / design_txt_filename

    events = build_events(song_title, schedule_txt_filename, design_txt_filename)

    DOWNLOADS_PATH.mkdir(parents=True, exist_ok=True)
    ics_path.write_text(create_ics(events), encoding="utf-8")
    schedule_txt_path.write_text(build_post_schedule_text(song_title, post_items), encoding="utf-8")
    design_txt_path.write_text(build_reel_design_text(song_title, post_items), encoding="utf-8")

    result_box.delete("1.0", tk.END)

    lines = [
        f"Created ICS: {ics_path}",
        f"Created schedule TXT: {schedule_txt_path}",
        f"Created design TXT: {design_txt_path}",
        "",
        "Calendar events:",
        "",
    ]

    for event in events:
        lines.append(f"{event['datetime'].strftime('%Y-%m-%d %H:%M')} - {event['title']}")

    lines.extend(["", "Post schedule:", ""])

    for item in post_items:
        lines.append(f"{item['date'].strftime('%Y-%m-%d')} 20:00 - {item['filename']}")

    result_box.insert(tk.END, "\n".join(lines))

    messagebox.showinfo(
        "Done",
        f"Files created:\n\n{ics_path}\n{schedule_txt_path}\n{design_txt_path}"
    )


def open_url(url):
    webbrowser.open(url)


root = tk.Tk()
root.title("Lukestrom Post Planner")
root.geometry("1220x900")
root.resizable(False, False)

main = ttk.Frame(root, padding=20)
main.pack(fill="both", expand=True)

song_title_var = tk.StringVar()

repost1_offset_var = tk.StringVar(value="3")
repost2_offset_var = tk.StringVar(value="7")
repost3_offset_var = tk.StringVar(value="13")
repost4_offset_var = tk.StringVar(value="22")
repost5_offset_var = tk.StringVar(value="32")
repost6_offset_var = tk.StringVar(value="44")

ttk.Label(main, text="Song title").grid(row=0, column=0, sticky="w")
ttk.Entry(main, width=60, textvariable=song_title_var).grid(row=1, column=0, columnspan=6, sticky="w", pady=(5, 15))

ttk.Label(main, text="Repost intervals in weeks, relative to initial post").grid(row=2, column=0, columnspan=6, sticky="w", pady=(0, 5))

intervals = [
    ("Repost 1", repost1_offset_var),
    ("Repost 2", repost2_offset_var),
    ("Repost 3", repost3_offset_var),
    ("Repost 4", repost4_offset_var),
    ("Repost 5", repost5_offset_var),
    ("Repost 6", repost6_offset_var),
]

for index, (label, variable) in enumerate(intervals):
    ttk.Label(main, text=label).grid(row=3, column=index, sticky="w", padx=(0, 15))
    ttk.Entry(main, width=8, textvariable=variable).grid(row=4, column=index, sticky="w", padx=(0, 15), pady=(5, 20))

headers = ["Posting moment", "First 2 seconds", "Opening text"]
for col, header in enumerate(headers):
    ttk.Label(main, text=header).grid(row=5, column=col, sticky="w", padx=(0, 10), pady=(0, 5))

posting_labels = [
    "Initial",
    "Repost 1",
    "Repost 2",
    "Repost 3",
    "Repost 4",
    "Repost 5",
    "Repost 6",
]

creative_boxes = []

start_row = 6

for i, label in enumerate(posting_labels):
    row = start_row + i

    ttk.Label(main, text=label).grid(row=row, column=0, sticky="nw", padx=(0, 10), pady=(0, 8))

    first_seconds_box = tk.Text(main, width=40, height=3, wrap="word")
    first_seconds_box.grid(row=row, column=1, sticky="w", padx=(0, 10), pady=(0, 8))

    opening_text_box = tk.Text(main, width=60, height=3, wrap="word")
    opening_text_box.grid(row=row, column=2, sticky="w", padx=(0, 10), pady=(0, 8))

    creative_boxes.append((first_seconds_box, opening_text_box))

(
    (initial_first_seconds_box, initial_opening_text_box),
    (repost1_first_seconds_box, repost1_opening_text_box),
    (repost2_first_seconds_box, repost2_opening_text_box),
    (repost3_first_seconds_box, repost3_opening_text_box),
    (repost4_first_seconds_box, repost4_opening_text_box),
    (repost5_first_seconds_box, repost5_opening_text_box),
    (repost6_first_seconds_box, repost6_opening_text_box),
) = creative_boxes

button_row = start_row + len(posting_labels)

ttk.Button(main, text="Generate ICS + TXT", command=generate).grid(row=button_row, column=0, sticky="w", pady=(10, 15))

ttk.Label(main, text="Result").grid(row=button_row + 1, column=0, sticky="w")

result_box = tk.Text(main, width=145, height=9, wrap="word")
result_box.grid(row=button_row + 2, column=0, columnspan=6, sticky="w", pady=(5, 0))

link_frame = ttk.Frame(main)
link_frame.grid(row=button_row + 3, column=0, columnspan=6, sticky="w", pady=(15, 0))

links = [
    ("DistroKid My Music", URL_DISTROKID),
    ("YouTube Uploads", URL_YOUTUBE),
    ("Facebook Posts", URL_FACEBOOK),
    ("TikTok Studio", URL_TIKTOK),
]

for idx, (text, url) in enumerate(links):
    link = tk.Label(
        link_frame,
        text=text,
        fg="blue",
        cursor="hand2",
        font=("Segoe UI", 9, "underline"),
    )
    link.grid(row=idx, column=0, sticky="w", pady=2)
    link.bind("<Button-1>", lambda e, u=url: open_url(u))

root.mainloop()
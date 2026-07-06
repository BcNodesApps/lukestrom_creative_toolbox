import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date, time, timedelta
from pathlib import Path
import uuid
import webbrowser


DOWNLOADS_PATH = Path.home() / "Downloads"

ARTIST_NAME = "LukeStrom"
YOUTUBE_HANDLE = "@lukestrommusic"
POST_TIME = time(20, 0)
POST_TIME_TEXT = "20:00"

URL_DISTROKID = "https://distrokid.com/mymusic/"
URL_YOUTUBE = "https://studio.youtube.com/channel/UCAUCC7uw_shkAmX7kPMy5IQ/videos/upload?d=ud&filter=%5B%5D&sort=%7B%22columnType%22%3A%22date%22%2C%22sortOrder%22%3A%22DESCENDING%22%7D"
URL_FACEBOOK = "https://business.facebook.com/latest/posts/published_posts/?business_id=678482264451473&asset_id=1126335547219736"
URL_TIKTOK = "https://www.tiktok.com/tiktokstudio/content"

DEFAULT_HASHTAGS = """#lukestrom
#meloverse
#originalmusic
#rockmusic
#breda"""

# Fixed campaign timing based on the schedule provided by John.
# These are day offsets relative to Post 1.
CAMPAIGN_ITEMS = [
    ("Post 1", 1, 0),
    ("Post 2", 2, 3),
    ("Post 3", 3, 8),
    ("Post 4", 4, 15),

    ("Repost 1 - Post 1", 1, 21),
    ("Repost 1 - Post 2", 2, 24),
    ("Repost 1 - Post 3", 3, 29),
    ("Repost 1 - Post 4", 4, 36),

    ("Repost 2 - Post 1", 1, 46),
    ("Repost 2 - Post 2", 2, 49),
    ("Repost 2 - Post 3", 3, 54),
    ("Repost 2 - Post 4", 4, 61),

    ("Repost 3 - Post 1", 1, 76),
    ("Repost 3 - Post 2", 2, 79),
    ("Repost 3 - Post 3", 3, 84),
    ("Repost 3 - Post 4", 4, 91),

    ("Repost 4 - Post 1", 1, 111),
    ("Repost 4 - Post 2", 2, 114),
    ("Repost 4 - Post 3", 3, 119),
    ("Repost 4 - Post 4", 4, 126),
]


def format_ics_datetime(dt: datetime) -> str:
    return dt.strftime("%Y%m%dT%H%M%S")


def safe_filename(text: str) -> str:
    return "_".join(text.strip().lower().split())


def display_song_filename(text: str) -> str:
    return " ".join(text.strip().split())


def clean_multiline(text: str) -> str:
    return text.strip() if text.strip() else "-"


def hashtags_to_single_line(hashtags: str) -> str:
    return " ".join(hashtags.split())


def build_caption(song_title: str, song_description: str, hashtags: str) -> str:
    hashtag_line = hashtags_to_single_line(hashtags)

    return (
        f"{ARTIST_NAME} - {song_title}\n\n"
        f"{song_description.strip()}\n\n"
        f"Join the MeloVerse!\n\n"
        f"🎧 Full video on YouTube {YOUTUBE_HANDLE}\n\n"
        f"{hashtag_line}"
    )


def get_song_title() -> str | None:
    song_title = song_title_var.get().strip()

    if not song_title:
        messagebox.showerror("Error", "Enter a song title.")
        return None

    return song_title


def get_output_filenames(song_title: str) -> dict:
    today = date.today()
    safe_title = safe_filename(song_title)
    date_prefix = today.strftime("%y%m%d")

    return {
        "ics_filename": f"{date_prefix}_{safe_title}_catalog.ics",
        "schedule_txt_filename": f"{date_prefix}_{safe_title}_post_schedule.txt",
        "design_txt_filename": f"{date_prefix}_{safe_title}_reel_design.txt",
    }


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


def build_campaign_items(song_title: str) -> list[dict]:
    post_1_date = date.today()
    filename_song = display_song_filename(song_title)

    items = []

    for label, post_number, day_offset in CAMPAIGN_ITEMS:
        items.append({
            "label": label,
            "post_number": post_number,
            "date": post_1_date + timedelta(days=day_offset),
            "filename": f"post {post_number} - {filename_song}.mp4",
        })

    return items


def build_creative_items(song_title: str) -> list[dict]:
    filename_song = display_song_filename(song_title)

    return [
        {
            "label": "Post 1",
            "filename": f"post 1 - {filename_song}.mp4",
            "first_seconds": post1_first_seconds_box.get("1.0", tk.END).strip(),
            "opening_text": post1_opening_text_box.get("1.0", tk.END).strip(),
        },
        {
            "label": "Post 2",
            "filename": f"post 2 - {filename_song}.mp4",
            "first_seconds": post2_first_seconds_box.get("1.0", tk.END).strip(),
            "opening_text": post2_opening_text_box.get("1.0", tk.END).strip(),
        },
        {
            "label": "Post 3",
            "filename": f"post 3 - {filename_song}.mp4",
            "first_seconds": post3_first_seconds_box.get("1.0", tk.END).strip(),
            "opening_text": post3_opening_text_box.get("1.0", tk.END).strip(),
        },
        {
            "label": "Post 4",
            "filename": f"post 4 - {filename_song}.mp4",
            "first_seconds": post4_first_seconds_box.get("1.0", tk.END).strip(),
            "opening_text": post4_opening_text_box.get("1.0", tk.END).strip(),
        },
    ]


def build_post_schedule_text(
    song_title: str,
    song_description: str,
    campaign_items: list[dict],
    hashtags: str,
) -> str:
    caption = build_caption(song_title, song_description, hashtags)

    lines = [
        f"Song: {song_title}",
        f"Artist: {ARTIST_NAME}",
        "",
        "POST SCHEDULE",
        "",
        "General instructions:",
        "- This file contains 20 content moments and 20 scheduling tasks.",
        "- Metricool handles cross-posting.",
        "- Each block is one scheduling task.",
        "- Schedule the block, then delete it from this file.",
        "- The first 2 seconds and opening text are already baked into the video.",
        "- Use the filename, date, time, and caption exactly as shown.",
        "",
        "URLs:",
        f"DistroKid: {URL_DISTROKID}",
        f"Meta Business Suite: {URL_FACEBOOK}",
        f"YouTube Uploads: {URL_YOUTUBE}",
        f"TikTok Studio: {URL_TIKTOK}",
        "",
        "=" * 70,
        "",
    ]

    for item in campaign_items:
        lines.extend([
            item["label"],
            f"Date: {item['date'].strftime('%d/%m/%Y')}",
            f"Time: {POST_TIME_TEXT}",
            f"Filename: {item['filename']}",
            "Caption:",
            caption,
            "",
            "-" * 70,
            "",
        ])

    return "\n".join(lines)


def build_reel_design_text(song_title: str, creative_items: list[dict]) -> str:
    lines = [
        f"Song: {song_title}",
        f"Artist: {ARTIST_NAME}",
        "",
        "REEL DESIGN",
        "",
        "Use this file to create the four reel/video files before scheduling the campaign.",
        "Only Post 1 to Post 4 need creative notes.",
        "Reposts use the same video files.",
        "",
        "=" * 70,
        "",
    ]

    for item in creative_items:
        lines.extend([
            item["label"],
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
            "datetime": datetime.combine(today, POST_TIME),
            "title": f"{song_title} - Publish on DistroKid",
            "description": (
                f"Song: {song_title}\n"
                f"Artist: {ARTIST_NAME}\n"
                f"Task: Publish on DistroKid\n\n"
                f"Upload the song to DistroKid.\n"
                f"Check title, artist name, credits, lyrics, artwork, and AI/vocal disclosure settings.\n\n"
                f"URL:\n{URL_DISTROKID}"
            ),
        },
        {
            "datetime": datetime.combine(today, POST_TIME),
            "title": f"{song_title} - Schedule campaign",
            "description": (
                f"Song: {song_title}\n"
                f"Artist: {ARTIST_NAME}\n"
                f"Task: Schedule full social media campaign\n\n"
                f"Open the schedule file:\n"
                f"{schedule_txt_filename}\n\n"
                f"Creative reference file:\n"
                f"{design_txt_filename}\n\n"
                f"This campaign contains 20 content moments and 20 scheduling tasks.\n"
                f"Metricool handles cross-posting.\n"
                f"Schedule everything at 20:00.\n\n"
                f"Meta Business Suite: {URL_FACEBOOK}\n"
                f"YouTube Uploads: {URL_YOUTUBE}\n"
                f"TikTok Studio: {URL_TIKTOK}"
            ),
        },
        {
            "datetime": datetime.combine(today + timedelta(days=1), POST_TIME),
            "title": f"{song_title} - Cleanup",
            "description": (
                f"Song: {song_title}\n"
                f"Artist: {ARTIST_NAME}\n"
                f"Task: Cleanup\n\n"
                f"- Verify all scheduled posts were created.\n"
                f"- Check the schedule file again if needed: {schedule_txt_filename}\n"
                f"- Store the creative reel design file: {design_txt_filename}\n"
                f"- Archive project files clearly.\n"
                f"- Remove temporary reel files if no longer needed."
            ),
        },
    ]


def export_reel_design():
    song_title = get_song_title()
    if song_title is None:
        return

    filenames = get_output_filenames(song_title)
    design_txt_path = DOWNLOADS_PATH / filenames["design_txt_filename"]
    creative_items = build_creative_items(song_title)

    DOWNLOADS_PATH.mkdir(parents=True, exist_ok=True)
    design_txt_path.write_text(build_reel_design_text(song_title, creative_items), encoding="utf-8")

    result_box.delete("1.0", tk.END)

    result_box.insert(
        tk.END,
        "\n".join([
            f"Created design TXT: {design_txt_path}",
            "",
            "Reel design exported only.",
            "No campaign schedule or calendar file was created.",
            "",
            "Next step:",
            "Create the four reel files listed in the design file.",
        ])
    )

    messagebox.showinfo(
        "Done",
        f"Reel design file created:\n\n{design_txt_path}"
    )


def generate_campaign():
    song_title = get_song_title()
    if song_title is None:
        return

    song_description = song_description_box.get("1.0", tk.END).strip()
    hashtags = hashtags_box.get("1.0", tk.END).strip()

    filenames = get_output_filenames(song_title)

    ics_filename = filenames["ics_filename"]
    schedule_txt_filename = filenames["schedule_txt_filename"]
    design_txt_filename = filenames["design_txt_filename"]

    ics_path = DOWNLOADS_PATH / ics_filename
    schedule_txt_path = DOWNLOADS_PATH / schedule_txt_filename

    campaign_items = build_campaign_items(song_title)
    events = build_events(song_title, schedule_txt_filename, design_txt_filename)

    DOWNLOADS_PATH.mkdir(parents=True, exist_ok=True)
    ics_path.write_text(create_ics(events), encoding="utf-8")
    schedule_txt_path.write_text(
        build_post_schedule_text(song_title, song_description, campaign_items, hashtags),
        encoding="utf-8"
    )

    result_box.delete("1.0", tk.END)

    lines = [
        f"Created ICS: {ics_path}",
        f"Created schedule TXT: {schedule_txt_path}",
        "",
        "Campaign generated.",
        "The reel design TXT was not regenerated by this button.",
        "",
        "Calendar events:",
        "",
    ]

    for event in events:
        lines.append(f"{event['datetime'].strftime('%Y-%m-%d %H:%M')} - {event['title']}")

    lines.extend([
        "",
        "Campaign:",
        "",
        "20 content moments",
        "20 scheduling tasks",
        "Metricool handles cross-posting",
        "",
        "Post schedule:",
        "",
    ])

    for item in campaign_items:
        lines.append(f"{item['date'].strftime('%d/%m/%Y')} 20:00 - {item['label']} - {item['filename']}")

    result_box.insert(tk.END, "\n".join(lines))

    messagebox.showinfo(
        "Done",
        f"Campaign files created:\n\n{ics_path}\n{schedule_txt_path}"
    )


def open_url(url):
    webbrowser.open(url)


root = tk.Tk()
root.title("LukeStrom Post Planner")
root.geometry("1220x900")
root.resizable(False, False)

main = ttk.Frame(root, padding=20)
main.pack(fill="both", expand=True)

song_title_var = tk.StringVar()

ttk.Label(main, text="Song title").grid(row=0, column=0, sticky="w")
ttk.Entry(main, width=60, textvariable=song_title_var).grid(row=1, column=0, columnspan=3, sticky="w", pady=(5, 10))

ttk.Label(main, text="Song Description").grid(row=2, column=0, sticky="w")
song_description_box = tk.Text(main, width=60, height=4, wrap="word")
song_description_box.grid(row=3, column=0, columnspan=3, sticky="w", pady=(5, 10))

ttk.Label(main, text="Hashtags").grid(row=4, column=0, sticky="w")
hashtags_box = tk.Text(main, width=60, height=5, wrap="word")
hashtags_box.grid(row=5, column=0, columnspan=3, sticky="w", pady=(5, 15))
hashtags_box.insert("1.0", DEFAULT_HASHTAGS)

ttk.Label(main, text="Creative reel design").grid(row=6, column=0, columnspan=3, sticky="w", pady=(0, 5))

headers = ["Post", "First 2 seconds", "Opening text"]
for col, header in enumerate(headers):
    ttk.Label(main, text=header).grid(row=7, column=col, sticky="w", padx=(0, 10), pady=(0, 5))

creative_boxes = []
posting_labels = ["Post 1", "Post 2", "Post 3", "Post 4"]
start_row = 8

for i, label in enumerate(posting_labels):
    row = start_row + i

    ttk.Label(main, text=label).grid(row=row, column=0, sticky="nw", padx=(0, 10), pady=(0, 8))

    first_seconds_box = tk.Text(main, width=40, height=4, wrap="word")
    first_seconds_box.grid(row=row, column=1, sticky="w", padx=(0, 10), pady=(0, 8))

    opening_text_box = tk.Text(main, width=60, height=4, wrap="word")
    opening_text_box.grid(row=row, column=2, sticky="w", padx=(0, 10), pady=(0, 8))

    creative_boxes.append((first_seconds_box, opening_text_box))

(
    (post1_first_seconds_box, post1_opening_text_box),
    (post2_first_seconds_box, post2_opening_text_box),
    (post3_first_seconds_box, post3_opening_text_box),
    (post4_first_seconds_box, post4_opening_text_box),
) = creative_boxes

button_row = start_row + len(posting_labels)

button_frame = ttk.Frame(main)
button_frame.grid(row=button_row, column=0, columnspan=3, sticky="w", pady=(10, 15))

ttk.Button(button_frame, text="Export Reel Design", command=export_reel_design).grid(row=0, column=0, sticky="w", padx=(0, 10))
ttk.Button(button_frame, text="Generate Campaign", command=generate_campaign).grid(row=0, column=1, sticky="w")

ttk.Label(main, text="Result").grid(row=button_row + 1, column=0, sticky="w")

result_box = tk.Text(main, width=145, height=12, wrap="word")
result_box.grid(row=button_row + 2, column=0, columnspan=3, sticky="w", pady=(5, 0))

link_frame = ttk.Frame(main)
link_frame.grid(row=button_row + 3, column=0, columnspan=3, sticky="w", pady=(15, 0))

links = [
    ("DistroKid My Music", URL_DISTROKID),
    ("Meta Business Suite", URL_FACEBOOK),
    ("YouTube Uploads", URL_YOUTUBE),
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
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date, time, timedelta
from pathlib import Path
from tkcalendar import DateEntry
import uuid


DOWNLOADS_PATH = Path.home() / "Downloads"

URL_TIKTOK = "https://www.tiktok.com/tiktokstudio/upload?from=webapp&lang=en-GB"
URL_YOUTUBE = "https://studio.youtube.com/channel/UCAUCC7uw_shkAmX7kPMy5IQ/videos/upload?d=ud&filter=%5B%5D&sort=%7B%22columnType%22%3A%22date%22%2C%22sortOrder%22%3A%22DESCENDING%22%7D"
URL_INSTAGRAM = "https://www.instagram.com/lukestrommusic/"
URL_FACEBOOK = "https://www.facebook.com/lukestrommusic/reels/"
URL_DISTROKID = "https://distrokid.com/new/"

HOOK_OPTIONS = [
    "Curiosity text",
    "Emotional text",
    "Dramatic text",
    "Question text",
    "Direct quote",
    "Confession style",
    "Wait-for-it intro",
    "Unexpected claim",
    "Tension opener",
    "No text opener",
]

PIVOT_OPTIONS = [
    "",
    "pivot 1",
    "pivot 2",
    "pivot 3",
    "pivot 4",
    "pivot 5",
]

HOUR_OPTIONS = [f"{h:02d}" for h in range(0, 24)]
MINUTE_OPTIONS = ["00", "15", "30", "45"]

TASK_DEFAULT_HOUR = 12
TASK_DEFAULT_MINUTE = 0

HOOK_REMINDER = (
    "Test only one thing: the hook text.\n\n"
    "Use the same base reel / same moment for 1a and 1b. "
    "Only change the hook text at the start.\n\n"
    "Evaluate after 24 hours. Primary metric: views. Secondary metric: like ratio."
)

REFRESH_REMINDER = (
    "Do not reuse the exact same reel. Refresh the winning hook concept with:\n"
    "- different opening frame\n"
    "- different shot order\n"
    "- different pacing\n"
    "- refreshed visuals"
)


def safe_song_title(title: str) -> str:
    return " ".join(title.strip().split()).lower()


def generate_output_name(title: str, start_date: datetime, pivot_version: str) -> str:
    safe_title = safe_song_title(title)
    date_prefix = start_date.strftime("%y%m%d")

    if pivot_version:
        pivot_prefix = pivot_version.replace("pivot ", "p")
        return f"{date_prefix}_{pivot_prefix}_{safe_title}_tester_schedule.ics"

    return f"{date_prefix}_{safe_title}_tester_schedule.ics"


def make_publish_datetime(d: date, hour_str: str, minute_str: str) -> datetime:
    return datetime.combine(d, time(int(hour_str), int(minute_str)))


def make_task_datetime(d: date) -> datetime:
    return datetime.combine(d, time(TASK_DEFAULT_HOUR, TASK_DEFAULT_MINUTE))


def format_user_datetime(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M")


def format_ics_datetime(dt: datetime) -> str:
    return dt.strftime("%Y%m%dT%H%M%S")


def task_title(song_title: str, task_text: str, pivot_version: str) -> str:
    if pivot_version:
        pivot_prefix = pivot_version.replace("pivot ", "p")
        return f"{pivot_prefix} - {song_title} - {task_text}"

    return f"{song_title} - {task_text}"


def add_task(schedule: list, task_dt: datetime, summary: str, description: str):
    schedule.append({
        "datetime": task_dt,
        "task": summary,
        "description": description,
    })


def add_task_on_date(schedule: list, task_date: date, summary: str, description: str):
    add_task(schedule, make_task_datetime(task_date), summary, description)


def create_ics_content(schedule: list[dict]) -> str:
    now_stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Lukestrom//Post Tester//EN",
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


def caption_prompt(song_title: str, option_names: list[str], repost: bool = False) -> str:
    options_text = "\n".join(option_names)

    if repost:
        return (
            f"Generate fresh captions for TikTok, YouTube Shorts, Instagram Reels, and Facebook Reels "
            f"for a refreshed repost of '{song_title}' using this winning hook concept:\n{options_text}\n\n"
            f"The caption should feel fresh, cinematic, emotional, and specific. "
            f"Do not make it generic. Also provide suitable hashtags per platform."
        )

    return (
        f"Generate captions for TikTok, YouTube Shorts, Instagram Reels, and Facebook Reels "
        f"for '{song_title}' using these hook test options:\n{options_text}\n\n"
        f"Keep the tone cinematic, emotional, and specific. "
        f"Do not make it generic. Also provide suitable hashtags per platform."
    )


def build_description(
    purpose: str,
    dimensions: list[str] | None = None,
    option_lines: list[str] | None = None,
    publish_lines: list[str] | None = None,
    prompt: str | None = None,
    urls: list[str] | None = None,
    pivot_version: str = "",
    pivot_notes: str = "",
    include_hook_reminder: bool = True,
    include_refresh_reminder: bool = False,
):
    lines = [f"Purpose: {purpose}", ""]

    if dimensions:
        lines.append("Dimensions:")
        lines.extend(dimensions)
        lines.append("")

    if option_lines:
        lines.append("Options:")
        lines.extend(option_lines)
        lines.append("")

    if publish_lines:
        lines.append("Publish moments:")
        lines.extend(publish_lines)
        lines.append("")

    if include_hook_reminder:
        lines.append("Reminder:")
        lines.append(HOOK_REMINDER)

    if include_refresh_reminder:
        lines.append("")
        lines.append("Refresh requirement:")
        lines.append(REFRESH_REMINDER)

    if prompt:
        lines.append("")
        lines.append("ChatGPT prompt:")
        lines.append(prompt)

    if urls:
        lines.append("")
        lines.append("URLs:")
        lines.extend(urls)

    if pivot_version and pivot_notes.strip():
        lines.append("")
        lines.append("Pivot / lessons learned:")
        lines.append(f"{pivot_version}")
        lines.append(pivot_notes.strip())

    return "\n".join(lines)


def build_option_lines(
    option_a_key: str,
    option_a_value: str,
    option_b_key: str | None = None,
    option_b_value: str | None = None,
) -> list[str]:
    lines = [option_a_key, option_a_value]

    if option_b_key and option_b_value:
        lines.extend(["", option_b_key, option_b_value])

    return lines


def calculate_key_dates(
    full_video_ready_date: date,
    distrokid_days_after_full_video: int,
    publish_dt_1a: datetime,
    publish_dt_1b: datetime,
) -> dict:
    distrokid_date = full_video_ready_date + timedelta(days=max(0, distrokid_days_after_full_video))

    create_and_schedule_hook_test_date = distrokid_date + timedelta(days=1)
    create_and_schedule_hook_test_dt = make_task_datetime(create_and_schedule_hook_test_date)

    review_1a_dt = publish_dt_1a + timedelta(hours=24)
    review_1b_dt = publish_dt_1b + timedelta(hours=24)

    crosspost_date = publish_dt_1a.date() + timedelta(days=3)
    refreshed_repost_date = publish_dt_1a.date() + timedelta(days=10)
    cleanup_date = refreshed_repost_date + timedelta(days=7)

    return {
        "distrokid_date": distrokid_date,
        "create_and_schedule_hook_test_date": create_and_schedule_hook_test_date,
        "create_and_schedule_hook_test_dt": create_and_schedule_hook_test_dt,
        "review_1a_dt": review_1a_dt,
        "review_1b_dt": review_1b_dt,
        "crosspost_date": crosspost_date,
        "refreshed_repost_date": refreshed_repost_date,
        "cleanup_date": cleanup_date,
    }


def validate_inputs(
    full_video_ready_date: date,
    distrokid_days_after_full_video: int,
    publish_dt_1a: datetime,
    publish_dt_1b: datetime,
) -> list[str]:
    errors = []

    if distrokid_days_after_full_video < 0:
        errors.append("Days from full video to DistroKid cannot be negative.")

    dates = calculate_key_dates(
        full_video_ready_date,
        distrokid_days_after_full_video,
        publish_dt_1a,
        publish_dt_1b,
    )

    schedule_hook_test_dt = dates["create_and_schedule_hook_test_dt"]

    if publish_dt_1a <= schedule_hook_test_dt:
        errors.append(
            "Option 1a publish moment is invalid.\n"
            f"It must be later than the create/post/schedule task:\n{format_user_datetime(schedule_hook_test_dt)}"
        )

    if publish_dt_1b <= publish_dt_1a:
        errors.append(
            "Option 1b publish moment is invalid.\n"
            "It must be later than option 1a."
        )

    if publish_dt_1b.date() != (publish_dt_1a.date() + timedelta(days=1)):
        errors.append(
            "Option 1b publish date is invalid.\n"
            "It must be exactly 1 day after option 1a."
        )

    crosspost_dt = make_task_datetime(dates["crosspost_date"])
    if crosspost_dt <= dates["review_1b_dt"]:
        errors.append(
            "Crosspost timing is invalid.\n"
            "Crosspost is Day +3 after option 1a, but it must happen after the 24h review of option 1b."
        )

    return errors


def build_tester_schedule(
    song_title: str,
    full_video_ready_date: date,
    distrokid_days_after_full_video: int,
    publish_dt_1a: datetime,
    publish_dt_1b: datetime,
    hook_a: str,
    hook_b: str,
    pivot_version: str,
    pivot_notes: str,
):
    schedule = []

    hook_a = hook_a.strip() or "Hook A"
    hook_b = hook_b.strip() or "Hook B"

    option_1a = hook_a
    option_1b = hook_b
    winning_hook_text = "Winning Hook"

    dates = calculate_key_dates(
        full_video_ready_date,
        distrokid_days_after_full_video,
        publish_dt_1a,
        publish_dt_1b,
    )

    add_task_on_date(
        schedule,
        full_video_ready_date,
        task_title(song_title, "create full video and cover", pivot_version),
        build_description(
            purpose="Create the full video and the YouTube cover.",
            dimensions=[
                "Full video: 3840x2160",
                "YouTube cover: 1280x720",
            ],
            pivot_version=pivot_version,
            pivot_notes=pivot_notes,
            include_hook_reminder=False,
        ),
    )

    add_task_on_date(
        schedule,
        dates["distrokid_date"],
        task_title(song_title, "publish on DistroKid", pivot_version),
        build_description(
            purpose="Publish the song on DistroKid and create the DistroKid cover.",
            dimensions=[
                "DistroKid cover: 3000x3000",
            ],
            urls=[URL_DISTROKID],
            pivot_version=pivot_version,
            pivot_notes=pivot_notes,
            include_hook_reminder=False,
        ),
    )

    add_task(
        schedule,
        dates["create_and_schedule_hook_test_dt"],
        task_title(song_title, "create, post and schedule hook test 1a and 1b on TikTok", pivot_version),
        build_description(
            purpose="Create both hook test reels, upload them to TikTok, and schedule them for their publishing moments.",
            dimensions=[
                "Reels: 1080x1920",
                "Testing cover: 1080x1920",
            ],
            option_lines=build_option_lines("option 1a hook", option_1a, "option 1b hook", option_1b),
            publish_lines=[
                f"option 1a: {format_user_datetime(publish_dt_1a)}",
                f"option 1b: {format_user_datetime(publish_dt_1b)}",
            ],
            prompt=caption_prompt(song_title, [f"option 1a hook: {option_1a}", f"option 1b hook: {option_1b}"]),
            urls=[URL_TIKTOK],
            pivot_version=pivot_version,
            pivot_notes=pivot_notes,
        ),
    )

    add_task(
        schedule,
        dates["review_1a_dt"],
        task_title(song_title, "review hook test option 1a", pivot_version),
        build_description(
            purpose="Check and review performance of option 1a exactly 24 hours after publishing.",
            option_lines=build_option_lines("option 1a hook", option_1a),
            publish_lines=[f"published: {format_user_datetime(publish_dt_1a)}"],
            pivot_version=pivot_version,
            pivot_notes=pivot_notes,
        ),
    )

    add_task(
        schedule,
        dates["review_1b_dt"],
        task_title(song_title, "review hook test option 1b and decide winning hook", pivot_version),
        build_description(
            purpose="Check and review performance of option 1b exactly 24 hours after publishing and decide the winning hook.",
            option_lines=build_option_lines("option 1b hook", option_1b),
            publish_lines=[f"published: {format_user_datetime(publish_dt_1b)}"],
            pivot_version=pivot_version,
            pivot_notes=pivot_notes,
        ),
    )

    add_task_on_date(
        schedule,
        dates["crosspost_date"],
        task_title(song_title, "crosspost winning hook reel", pivot_version),
        build_description(
            purpose="Crosspost the winning TikTok reel to YouTube Shorts, Instagram Reels, and Facebook Reels.",
            option_lines=["winning hook", winning_hook_text],
            prompt=caption_prompt(song_title, [f"winning hook: {winning_hook_text}"]),
            urls=[URL_YOUTUBE, URL_INSTAGRAM, URL_FACEBOOK],
            pivot_version=pivot_version,
            pivot_notes=pivot_notes,
        ),
    )

    add_task_on_date(
        schedule,
        dates["refreshed_repost_date"],
        task_title(song_title, "create refreshed repost of winning hook", pivot_version),
        build_description(
            purpose="Create and publish a refreshed repost based on the winning hook concept.",
            dimensions=[
                "Refreshed repost reel: 1080x1920",
                "Refreshed repost cover: 1080x1920",
            ],
            option_lines=["winning hook concept", winning_hook_text],
            prompt=caption_prompt(song_title, [f"winning hook concept: {winning_hook_text}"], repost=True),
            urls=[URL_TIKTOK, URL_YOUTUBE, URL_INSTAGRAM, URL_FACEBOOK],
            pivot_version=pivot_version,
            pivot_notes=pivot_notes,
            include_refresh_reminder=True,
        ),
    )

    add_task_on_date(
        schedule,
        dates["cleanup_date"],
        task_title(song_title, "cleanup files", pivot_version),
        build_description(
            purpose="Cleanup files, review results, remove completed calendar items, and archive or organize assets.",
            pivot_version=pivot_version,
            pivot_notes=pivot_notes,
            include_hook_reminder=False,
        ),
    )

    schedule.sort(key=lambda x: x["datetime"])
    return schedule


def on_pivot_change(event=None):
    selected = pivot_var.get().strip()

    if selected:
        pivot_notes_label.grid()
        pivot_notes_box.grid()
    else:
        pivot_notes_label.grid_remove()
        pivot_notes_box.grid_remove()
        pivot_notes_box.delete("1.0", tk.END)


def update_default_dates(event=None):
    first_publish_date = posting_date_reel_a_entry.get_date()
    posting_date_reel_b_entry.set_date(first_publish_date + timedelta(days=1))


def run_tester():
    title = title_var.get().strip()

    if not title:
        messagebox.showerror("Error", "Please enter a song title.")
        return

    try:
        distrokid_days_after_full_video = int(distrokid_days_var.get())
    except ValueError:
        messagebox.showerror("Error", "Days from full video to DistroKid must be a whole number.")
        return

    full_video_ready_date = full_video_ready_date_entry.get_date()
    posting_date_reel_a = posting_date_reel_a_entry.get_date()
    posting_date_reel_b = posting_date_reel_b_entry.get_date()

    publish_dt_1a = make_publish_datetime(posting_date_reel_a, reel_a_hour_var.get(), reel_a_minute_var.get())
    publish_dt_1b = make_publish_datetime(posting_date_reel_b, reel_b_hour_var.get(), reel_b_minute_var.get())

    errors = validate_inputs(
        full_video_ready_date,
        distrokid_days_after_full_video,
        publish_dt_1a,
        publish_dt_1b,
    )

    if errors:
        messagebox.showerror("Invalid publish moment", "\n\n".join(errors))
        return

    pivot_version = pivot_var.get().strip()
    pivot_notes = pivot_notes_box.get("1.0", tk.END).strip() if pivot_version else ""

    start_date_dt = datetime.combine(full_video_ready_date, datetime.min.time())
    output_name = generate_output_name(title, start_date_dt, pivot_version)
    output_path = DOWNLOADS_PATH / output_name

    schedule = build_tester_schedule(
        song_title=title,
        full_video_ready_date=full_video_ready_date,
        distrokid_days_after_full_video=distrokid_days_after_full_video,
        publish_dt_1a=publish_dt_1a,
        publish_dt_1b=publish_dt_1b,
        hook_a=hook_a_var.get(),
        hook_b=hook_b_var.get(),
        pivot_version=pivot_version,
        pivot_notes=pivot_notes,
    )

    ics_content = create_ics_content(schedule)
    output_path.write_text(ics_content, encoding="utf-8")

    lines = [
        f"Title: {title}",
        f"Full video ready date: {full_video_ready_date.strftime('%Y-%m-%d')}",
        f"Pivot version: {pivot_version if pivot_version else 'none'}",
        f"Output file: {output_path}",
        "",
        "Schedule details:",
        "",
    ]

    for item in schedule:
        lines.append("=" * 90)
        lines.append(f"{item['datetime'].strftime('%Y-%m-%d %H:%M')}  {item['task']}")
        lines.append("")
        lines.append(item["description"])
        lines.append("")

    result_box.delete("1.0", tk.END)
    result_box.insert(tk.END, "\n".join(lines))
    messagebox.showinfo("Done", f"ICS file created:\n{output_path}")


root = tk.Tk()
root.title("Post Tester")
root.geometry("1220x900")
root.resizable(False, False)

main_frame = ttk.Frame(root, padding=20)
main_frame.pack(fill="both", expand=True)

title_var = tk.StringVar()
distrokid_days_var = tk.StringVar(value="2")

hook_a_var = tk.StringVar(value=HOOK_OPTIONS[0])
hook_b_var = tk.StringVar(value=HOOK_OPTIONS[4])

pivot_var = tk.StringVar(value="")

today = date.today()
reel_a_default = today + timedelta(days=5)
reel_b_default = today + timedelta(days=6)

reel_a_hour_var = tk.StringVar(value="20")
reel_a_minute_var = tk.StringVar(value="00")
reel_b_hour_var = tk.StringVar(value="20")
reel_b_minute_var = tk.StringVar(value="00")

# Left column
row = 0

ttk.Label(main_frame, text="Song title").grid(row=row, column=0, sticky="w", pady=(0, 5))
ttk.Entry(main_frame, width=42, textvariable=title_var).grid(row=row + 1, column=0, sticky="w", pady=(0, 10))

row += 2

ttk.Label(main_frame, text="Start date (full video ready)").grid(row=row, column=0, sticky="w", pady=(0, 5))
full_video_ready_date_entry = DateEntry(main_frame, width=18, date_pattern="yyyy-mm-dd")
full_video_ready_date_entry.grid(row=row + 1, column=0, sticky="w", pady=(0, 10))
full_video_ready_date_entry.set_date(today)

row += 2

ttk.Label(main_frame, text="Days from full video to DistroKid").grid(row=row, column=0, sticky="w", pady=(0, 5))
ttk.Entry(main_frame, width=10, textvariable=distrokid_days_var).grid(row=row + 1, column=0, sticky="w", pady=(0, 10))

row += 2

ttk.Label(main_frame, text="Publish date option 1a").grid(row=row, column=0, sticky="w", pady=(0, 5))
posting_date_reel_a_entry = DateEntry(main_frame, width=18, date_pattern="yyyy-mm-dd")
posting_date_reel_a_entry.grid(row=row + 1, column=0, sticky="w", pady=(0, 8))
posting_date_reel_a_entry.set_date(reel_a_default)
posting_date_reel_a_entry.bind("<<DateEntrySelected>>", update_default_dates)

ttk.Label(main_frame, text="Publish time option 1a").grid(row=row, column=1, sticky="w", pady=(0, 5))
ttk.Combobox(main_frame, width=4, textvariable=reel_a_hour_var, values=HOUR_OPTIONS, state="readonly").grid(row=row + 1, column=1, sticky="w", pady=(0, 8))
ttk.Combobox(main_frame, width=4, textvariable=reel_a_minute_var, values=MINUTE_OPTIONS, state="readonly").grid(row=row + 1, column=1, sticky="w", padx=(60, 0), pady=(0, 8))

row += 2

ttk.Label(main_frame, text="Publish date option 1b").grid(row=row, column=0, sticky="w", pady=(0, 5))
posting_date_reel_b_entry = DateEntry(main_frame, width=18, date_pattern="yyyy-mm-dd")
posting_date_reel_b_entry.grid(row=row + 1, column=0, sticky="w", pady=(0, 8))
posting_date_reel_b_entry.set_date(reel_b_default)

ttk.Label(main_frame, text="Publish time option 1b").grid(row=row, column=1, sticky="w", pady=(0, 5))
ttk.Combobox(main_frame, width=4, textvariable=reel_b_hour_var, values=HOUR_OPTIONS, state="readonly").grid(row=row + 1, column=1, sticky="w", pady=(0, 8))
ttk.Combobox(main_frame, width=4, textvariable=reel_b_minute_var, values=MINUTE_OPTIONS, state="readonly").grid(row=row + 1, column=1, sticky="w", padx=(60, 0), pady=(0, 8))

# Right column
right_pad = 50

ttk.Label(main_frame, text="Hook A").grid(row=0, column=2, sticky="w", padx=(right_pad, 0), pady=(0, 5))
ttk.Combobox(main_frame, width=30, textvariable=hook_a_var, values=HOOK_OPTIONS, state="readonly").grid(row=1, column=2, sticky="w", padx=(right_pad, 0), pady=(0, 10))

ttk.Label(main_frame, text="Hook B").grid(row=2, column=2, sticky="w", padx=(right_pad, 0), pady=(0, 5))
ttk.Combobox(main_frame, width=30, textvariable=hook_b_var, values=HOOK_OPTIONS, state="readonly").grid(row=3, column=2, sticky="w", padx=(right_pad, 0), pady=(0, 10))

ttk.Label(main_frame, text="Pivot version").grid(row=4, column=2, sticky="w", padx=(right_pad, 0), pady=(0, 5))
pivot_combo = ttk.Combobox(main_frame, width=30, textvariable=pivot_var, values=PIVOT_OPTIONS, state="readonly")
pivot_combo.grid(row=5, column=2, sticky="w", padx=(right_pad, 0), pady=(0, 10))
pivot_combo.bind("<<ComboboxSelected>>", on_pivot_change)

pivot_notes_label = ttk.Label(main_frame, text="Pivot / lessons learned notes")
pivot_notes_label.grid(row=6, column=2, sticky="w", padx=(right_pad, 0), pady=(0, 5))

pivot_notes_box = tk.Text(main_frame, width=42, height=6, wrap="word")
pivot_notes_box.grid(row=7, column=2, rowspan=2, sticky="w", padx=(right_pad, 0), pady=(0, 10))

ttk.Label(main_frame, text="Fixed intervals used").grid(row=9, column=2, sticky="w", padx=(right_pad, 0), pady=(0, 5))
fixed_info = (
    "Hook test 1a: chosen publish date\n"
    "Hook test 1b: always 1 day after 1a\n"
    "Review items: exactly 24 hours after publish datetime\n"
    "Crosspost winner: Day +3 after 1a\n"
    "Refreshed repost: Day +10 after 1a\n"
    "Cleanup after refreshed repost: always 7 days"
)
ttk.Label(main_frame, text=fixed_info, justify="left").grid(
    row=10, column=2, rowspan=4, sticky="nw", padx=(right_pad, 0), pady=(0, 10)
)

ttk.Label(main_frame, text="Workflow").grid(row=12, column=0, sticky="w", pady=(20, 5))
workflow_info = (
    "1. Hook Test: 1a Day 0, 1b Day +1. Same base reel, different hook text only.\n"
    "2. Crosspost Winner: Day +3 after 1a to IG, FB, and YouTube Shorts.\n"
    "3. Refreshed Repost: Day +10 after 1a. Do not reuse the exact same reel."
)
ttk.Label(main_frame, text=workflow_info, justify="left").grid(row=13, column=0, columnspan=2, sticky="w", pady=(0, 15))

ttk.Button(main_frame, text="Generate", command=run_tester).grid(row=14, column=0, sticky="w", pady=(0, 15))

ttk.Label(main_frame, text="Result").grid(row=15, column=0, sticky="w")

result_box = tk.Text(main_frame, width=145, height=24, wrap="word")
result_box.grid(row=16, column=0, columnspan=4, sticky="nsew")

scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=result_box.yview)
scrollbar.grid(row=16, column=4, sticky="ns")
result_box.configure(yscrollcommand=scrollbar.set)

on_pivot_change()
root.mainloop()

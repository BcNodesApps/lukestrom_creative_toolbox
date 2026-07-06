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

MOMENT_OPTIONS = [
    "Wide cinematic scene",
    "Close-up face",
    "Walking shot",
    "Band wide shot",
    "Instrument close-up",
    "Chorus hit",
    "Verse storytelling",
    "Emotional vocal line",
    "Drop / beat kick-in",
    "Character reveal",
    "Two-person tension shot",
    "Walking away shot",
]

HOUR_OPTIONS = [f"{h:02d}" for h in range(0, 24)]
MINUTE_OPTIONS = ["00", "15", "30", "45"]

TASK_DEFAULT_HOUR = 12
TASK_DEFAULT_MINUTE = 0

HOOK_MOMENT_REMINDER = (
    "The hook is the entry, the text on screen, the first impression of what’s happening.\n\n"
    "The moment is the visual + part of the song you choose. It is: what is happening in the video, "
    "which part of the track plays, the emotional situation."
)


def safe_song_title(title: str) -> str:
    return " ".join(title.strip().split()).lower()


def generate_output_name(title: str, start_date: datetime) -> str:
    safe_title = safe_song_title(title)
    date_prefix = start_date.strftime("%y%m%d")
    return f"{date_prefix}_{safe_title}_tester_schedule.ics"


def make_publish_datetime(d: date, hour_str: str, minute_str: str) -> datetime:
    return datetime.combine(d, time(int(hour_str), int(minute_str)))


def make_task_datetime(d: date) -> datetime:
    return datetime.combine(d, time(TASK_DEFAULT_HOUR, TASK_DEFAULT_MINUTE))


def format_user_datetime(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M")


def format_ics_datetime(dt: datetime) -> str:
    return dt.strftime("%Y%m%dT%H%M%S")


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
            f"Generate new captions for TikTok, YouTube Shorts, Instagram Reels, and Facebook Reels "
            f"for reposting '{song_title}' using this winning combo:\n{options_text}\n\n"
            f"The caption should feel fresh, cinematic, emotional, and specific. "
            f"Do not make it generic. Also provide suitable hashtags per platform."
        )

    return (
        f"Generate captions for TikTok, YouTube Shorts, Instagram Reels, and Facebook Reels "
        f"for '{song_title}' using these options:\n{options_text}\n\n"
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

    lines.append("Reminder:")
    lines.append(HOOK_MOMENT_REMINDER)

    if prompt:
        lines.append("")
        lines.append("ChatGPT prompt:")
        lines.append(prompt)

    if urls:
        lines.append("")
        lines.append("URLs:")
        lines.extend(urls)

    return "\n".join(lines)


def combo_label(hook: str, moment: str) -> str:
    return f"{hook} + {moment}"


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
    publish_dt_2a: datetime,
    publish_dt_2b: datetime,
) -> dict:
    distrokid_date = full_video_ready_date + timedelta(days=max(0, distrokid_days_after_full_video))
    create_options_1_date = distrokid_date + timedelta(days=1)
    schedule_options_1_date = create_options_1_date + timedelta(days=1)
    schedule_options_1_dt = make_task_datetime(schedule_options_1_date)

    review_1a_dt = publish_dt_1a + timedelta(hours=24)
    review_1b_dt = publish_dt_1b + timedelta(hours=24)

    create_options_2_date = review_1b_dt.date() + timedelta(days=1)
    schedule_options_2_date = create_options_2_date + timedelta(days=1)
    schedule_options_2_dt = make_task_datetime(schedule_options_2_date)

    review_2a_dt = publish_dt_2a + timedelta(hours=24)
    review_2b_dt = publish_dt_2b + timedelta(hours=24)

    crosspost_date = review_2b_dt.date() + timedelta(days=1)
    repost_1_date = crosspost_date + timedelta(days=7)
    repost_2_date = crosspost_date + timedelta(days=14)
    cleanup_date = repost_2_date + timedelta(days=7)

    return {
        "distrokid_date": distrokid_date,
        "create_options_1_date": create_options_1_date,
        "schedule_options_1_date": schedule_options_1_date,
        "schedule_options_1_dt": schedule_options_1_dt,
        "review_1a_dt": review_1a_dt,
        "review_1b_dt": review_1b_dt,
        "create_options_2_date": create_options_2_date,
        "schedule_options_2_date": schedule_options_2_date,
        "schedule_options_2_dt": schedule_options_2_dt,
        "review_2a_dt": review_2a_dt,
        "review_2b_dt": review_2b_dt,
        "crosspost_date": crosspost_date,
        "repost_1_date": repost_1_date,
        "repost_2_date": repost_2_date,
        "cleanup_date": cleanup_date,
    }


def validate_inputs(
    full_video_ready_date: date,
    distrokid_days_after_full_video: int,
    publish_dt_1a: datetime,
    publish_dt_1b: datetime,
    publish_dt_2a: datetime,
    publish_dt_2b: datetime,
) -> list[str]:
    errors = []

    if distrokid_days_after_full_video < 0:
        errors.append("Days from full video to DistroKid cannot be negative.")

    dates = calculate_key_dates(
        full_video_ready_date,
        distrokid_days_after_full_video,
        publish_dt_1a,
        publish_dt_1b,
        publish_dt_2a,
        publish_dt_2b,
    )

    schedule_options_1_dt = dates["schedule_options_1_dt"]
    schedule_options_2_dt = dates["schedule_options_2_dt"]

    if publish_dt_1a <= schedule_options_1_dt:
        errors.append(
            "Option 1a publish moment is invalid.\n"
            f"It must be later than the scheduling task:\n{format_user_datetime(schedule_options_1_dt)}"
        )

    if publish_dt_1b <= schedule_options_1_dt:
        errors.append(
            "Option 1b publish moment is invalid.\n"
            f"It must be later than the scheduling task:\n{format_user_datetime(schedule_options_1_dt)}"
        )

    if publish_dt_2a <= schedule_options_2_dt:
        errors.append(
            "Option 2a publish moment is invalid.\n"
            f"It must be later than the scheduling task:\n{format_user_datetime(schedule_options_2_dt)}"
        )

    if publish_dt_2b <= schedule_options_2_dt:
        errors.append(
            "Option 2b publish moment is invalid.\n"
            f"It must be later than the scheduling task:\n{format_user_datetime(schedule_options_2_dt)}"
        )

    return errors


def build_tester_schedule(
    song_title: str,
    full_video_ready_date: date,
    distrokid_days_after_full_video: int,
    publish_dt_1a: datetime,
    publish_dt_1b: datetime,
    publish_dt_2a: datetime,
    publish_dt_2b: datetime,
    hook_a: str,
    hook_b: str,
    moment_a: str,
    moment_b: str,
):
    schedule = []

    hook_a = hook_a.strip() or "Hook A"
    hook_b = hook_b.strip() or "Hook B"
    moment_a = moment_a.strip() or "Moment A"
    moment_b = moment_b.strip() or "Moment B"

    option_1a = combo_label(hook_a, moment_a)
    option_1b = combo_label(hook_b, moment_a)
    option_2a = combo_label("Winning Hook", moment_a)
    option_2b = combo_label("Winning Hook", moment_b)
    winning_combo_text = "Winning Combo"

    dates = calculate_key_dates(
        full_video_ready_date,
        distrokid_days_after_full_video,
        publish_dt_1a,
        publish_dt_1b,
        publish_dt_2a,
        publish_dt_2b,
    )

    add_task_on_date(
        schedule,
        full_video_ready_date,
        f"{song_title} - create full video and cover",
        build_description(
            purpose="Create the full video and the YouTube cover.",
            dimensions=[
                "Full video: 3840x2160",
                "YouTube cover: 1280x720",
            ],
        ),
    )

    add_task_on_date(
        schedule,
        dates["distrokid_date"],
        f"{song_title} - publish on DistroKid",
        build_description(
            purpose="Publish the song on DistroKid and create the DistroKid cover.",
            dimensions=[
                "DistroKid cover: 3000x3000",
            ],
            urls=[URL_DISTROKID],
        ),
    )

    add_task_on_date(
        schedule,
        dates["create_options_1_date"],
        f"{song_title} - create option 1a and 1b reels",
        build_description(
            purpose="Create the first two test reels and the shared testing cover.",
            dimensions=[
                "Reels: 1080x1920",
                "Testing cover: 1080x1920",
            ],
            option_lines=build_option_lines("option 1a", option_1a, "option 1b", option_1b),
        ),
    )

    add_task(
        schedule,
        dates["schedule_options_1_dt"],
        f"{song_title} - post and schedule option 1a and 1b on TikTok",
        build_description(
            purpose="Upload both first-round TikTok reels and schedule them for their publishing moments.",
            option_lines=build_option_lines("option 1a", option_1a, "option 1b", option_1b),
            publish_lines=[
                f"option 1a: {format_user_datetime(publish_dt_1a)}",
                f"option 1b: {format_user_datetime(publish_dt_1b)}",
            ],
            prompt=caption_prompt(song_title, [f"option 1a: {option_1a}", f"option 1b: {option_1b}"]),
            urls=[URL_TIKTOK],
        ),
    )

    add_task(
        schedule,
        dates["review_1a_dt"],
        f"{song_title} - review option 1a",
        build_description(
            purpose="Check and review performance of option 1a exactly 24 hours after publishing.",
            option_lines=build_option_lines("option 1a", option_1a),
            publish_lines=[f"published: {format_user_datetime(publish_dt_1a)}"],
        ),
    )

    add_task(
        schedule,
        dates["review_1b_dt"],
        f"{song_title} - review option 1b and decide winning hook",
        build_description(
            purpose="Check and review performance of option 1b exactly 24 hours after publishing and decide the winning hook.",
            option_lines=build_option_lines("option 1b", option_1b),
            publish_lines=[f"published: {format_user_datetime(publish_dt_1b)}"],
        ),
    )

    add_task_on_date(
        schedule,
        dates["create_options_2_date"],
        f"{song_title} - create option 2a and 2b reels",
        build_description(
            purpose="Create the second two test reels based on the winning hook.",
            dimensions=[
                "Reels: 1080x1920",
                "Testing cover: 1080x1920",
            ],
            option_lines=build_option_lines("option 2a", option_2a, "option 2b", option_2b),
        ),
    )

    add_task(
        schedule,
        dates["schedule_options_2_dt"],
        f"{song_title} - post and schedule option 2a and 2b on TikTok",
        build_description(
            purpose="Upload both second-round TikTok reels and schedule them for their publishing moments.",
            option_lines=build_option_lines("option 2a", option_2a, "option 2b", option_2b),
            publish_lines=[
                f"option 2a: {format_user_datetime(publish_dt_2a)}",
                f"option 2b: {format_user_datetime(publish_dt_2b)}",
            ],
            prompt=caption_prompt(song_title, [f"option 2a: {option_2a}", f"option 2b: {option_2b}"]),
            urls=[URL_TIKTOK],
        ),
    )

    add_task(
        schedule,
        dates["review_2a_dt"],
        f"{song_title} - review option 2a",
        build_description(
            purpose="Check and review performance of option 2a exactly 24 hours after publishing.",
            option_lines=build_option_lines("option 2a", option_2a),
            publish_lines=[f"published: {format_user_datetime(publish_dt_2a)}"],
        ),
    )

    add_task(
        schedule,
        dates["review_2b_dt"],
        f"{song_title} - review option 2b and decide winning combo",
        build_description(
            purpose="Check and review performance of option 2b exactly 24 hours after publishing and decide the winning combo.",
            option_lines=build_option_lines("option 2b", option_2b),
            publish_lines=[f"published: {format_user_datetime(publish_dt_2b)}"],
        ),
    )

    add_task_on_date(
        schedule,
        dates["crosspost_date"],
        f"{song_title} - crosspost winning combo",
        build_description(
            purpose="Crosspost the winning combo on TikTok, YouTube Shorts, Instagram Reels, and Facebook Reels.",
            option_lines=["winning combo", winning_combo_text],
            prompt=caption_prompt(song_title, [f"winning combo: {winning_combo_text}"]),
            urls=[URL_TIKTOK, URL_YOUTUBE, URL_INSTAGRAM, URL_FACEBOOK],
        ),
    )

    add_task_on_date(
        schedule,
        dates["repost_1_date"],
        f"{song_title} - repost winning combo",
        build_description(
            purpose="Cross repost the winning combo with a new cover and new caption.",
            dimensions=[
                "Repost cover: 1080x1920",
            ],
            option_lines=["winning combo", winning_combo_text],
            prompt=caption_prompt(song_title, [f"winning combo: {winning_combo_text}"], repost=True),
            urls=[URL_TIKTOK, URL_YOUTUBE, URL_INSTAGRAM, URL_FACEBOOK],
        ),
    )

    add_task_on_date(
        schedule,
        dates["repost_2_date"],
        f"{song_title} - repost winning combo again",
        build_description(
            purpose="Cross repost the winning combo again with a new cover and new caption.",
            dimensions=[
                "Repost cover: 1080x1920",
            ],
            option_lines=["winning combo", winning_combo_text],
            prompt=caption_prompt(song_title, [f"winning combo: {winning_combo_text}"], repost=True),
            urls=[URL_TIKTOK, URL_YOUTUBE, URL_INSTAGRAM, URL_FACEBOOK],
        ),
    )

    add_task_on_date(
        schedule,
        dates["cleanup_date"],
        f"{song_title} - cleanup files",
        build_description(
            purpose="Cleanup files, review results, remove completed calendar items, and archive or organize assets.",
        ),
    )

    schedule.sort(key=lambda x: x["datetime"])
    return schedule


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
    posting_date_winner_a = posting_date_winner_a_entry.get_date()
    posting_date_winner_b = posting_date_winner_b_entry.get_date()

    publish_dt_1a = make_publish_datetime(posting_date_reel_a, reel_a_hour_var.get(), reel_a_minute_var.get())
    publish_dt_1b = make_publish_datetime(posting_date_reel_b, reel_b_hour_var.get(), reel_b_minute_var.get())
    publish_dt_2a = make_publish_datetime(posting_date_winner_a, winner_a_hour_var.get(), winner_a_minute_var.get())
    publish_dt_2b = make_publish_datetime(posting_date_winner_b, winner_b_hour_var.get(), winner_b_minute_var.get())

    errors = validate_inputs(
        full_video_ready_date,
        distrokid_days_after_full_video,
        publish_dt_1a,
        publish_dt_1b,
        publish_dt_2a,
        publish_dt_2b,
    )

    if errors:
        messagebox.showerror("Invalid publish moment", "\n\n".join(errors))
        return

    start_date_dt = datetime.combine(full_video_ready_date, datetime.min.time())
    output_name = generate_output_name(title, start_date_dt)
    output_path = DOWNLOADS_PATH / output_name

    schedule = build_tester_schedule(
        song_title=title,
        full_video_ready_date=full_video_ready_date,
        distrokid_days_after_full_video=distrokid_days_after_full_video,
        publish_dt_1a=publish_dt_1a,
        publish_dt_1b=publish_dt_1b,
        publish_dt_2a=publish_dt_2a,
        publish_dt_2b=publish_dt_2b,
        hook_a=hook_a_var.get(),
        hook_b=hook_b_var.get(),
        moment_a=moment_a_var.get(),
        moment_b=moment_b_var.get(),
    )

    ics_content = create_ics_content(schedule)
    output_path.write_text(ics_content, encoding="utf-8")

    lines = [
        f"Title: {title}",
        f"Full video ready date: {full_video_ready_date.strftime('%Y-%m-%d')}",
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
root.geometry("1320x980")
root.resizable(False, False)

main_frame = ttk.Frame(root, padding=20)
main_frame.pack(fill="both", expand=True)

title_var = tk.StringVar()
distrokid_days_var = tk.StringVar(value="2")

hook_a_var = tk.StringVar(value=HOOK_OPTIONS[0])
hook_b_var = tk.StringVar(value=HOOK_OPTIONS[4])
moment_a_var = tk.StringVar(value=MOMENT_OPTIONS[6])
moment_b_var = tk.StringVar(value=MOMENT_OPTIONS[5])

today = date.today()
reel_a_default = today + timedelta(days=5)
reel_b_default = today + timedelta(days=6)
winner_a_default = today + timedelta(days=10)
winner_b_default = today + timedelta(days=11)

reel_a_hour_var = tk.StringVar(value="20")
reel_a_minute_var = tk.StringVar(value="00")
reel_b_hour_var = tk.StringVar(value="20")
reel_b_minute_var = tk.StringVar(value="00")
winner_a_hour_var = tk.StringVar(value="20")
winner_a_minute_var = tk.StringVar(value="00")
winner_b_hour_var = tk.StringVar(value="20")
winner_b_minute_var = tk.StringVar(value="00")

# Left column
ttk.Label(main_frame, text="Song title").grid(row=0, column=0, sticky="w", pady=(0, 5))
ttk.Entry(main_frame, width=42, textvariable=title_var).grid(row=1, column=0, sticky="w", pady=(0, 10))

ttk.Label(main_frame, text="Start date (full video ready)").grid(row=2, column=0, sticky="w", pady=(0, 5))
full_video_ready_date_entry = DateEntry(main_frame, width=18, date_pattern="yyyy-mm-dd")
full_video_ready_date_entry.grid(row=3, column=0, sticky="w", pady=(0, 10))
full_video_ready_date_entry.set_date(today)

ttk.Label(main_frame, text="Days from full video to DistroKid").grid(row=4, column=0, sticky="w", pady=(0, 5))
ttk.Entry(main_frame, width=10, textvariable=distrokid_days_var).grid(row=5, column=0, sticky="w", pady=(0, 10))

ttk.Label(main_frame, text="Publish date option 1a").grid(row=6, column=0, sticky="w", pady=(0, 5))
posting_date_reel_a_entry = DateEntry(main_frame, width=18, date_pattern="yyyy-mm-dd")
posting_date_reel_a_entry.grid(row=7, column=0, sticky="w", pady=(0, 8))
posting_date_reel_a_entry.set_date(reel_a_default)

ttk.Label(main_frame, text="Publish time option 1a").grid(row=6, column=1, sticky="w", pady=(0, 5))
ttk.Combobox(main_frame, width=4, textvariable=reel_a_hour_var, values=HOUR_OPTIONS, state="readonly").grid(row=7, column=1, sticky="w", pady=(0, 8))
ttk.Combobox(main_frame, width=4, textvariable=reel_a_minute_var, values=MINUTE_OPTIONS, state="readonly").grid(row=7, column=1, sticky="w", padx=(60, 0), pady=(0, 8))

ttk.Label(main_frame, text="Publish date option 1b").grid(row=8, column=0, sticky="w", pady=(0, 5))
posting_date_reel_b_entry = DateEntry(main_frame, width=18, date_pattern="yyyy-mm-dd")
posting_date_reel_b_entry.grid(row=9, column=0, sticky="w", pady=(0, 8))
posting_date_reel_b_entry.set_date(reel_b_default)

ttk.Label(main_frame, text="Publish time option 1b").grid(row=8, column=1, sticky="w", pady=(0, 5))
ttk.Combobox(main_frame, width=4, textvariable=reel_b_hour_var, values=HOUR_OPTIONS, state="readonly").grid(row=9, column=1, sticky="w", pady=(0, 8))
ttk.Combobox(main_frame, width=4, textvariable=reel_b_minute_var, values=MINUTE_OPTIONS, state="readonly").grid(row=9, column=1, sticky="w", padx=(60, 0), pady=(0, 8))

ttk.Label(main_frame, text="Publish date option 2a").grid(row=10, column=0, sticky="w", pady=(0, 5))
posting_date_winner_a_entry = DateEntry(main_frame, width=18, date_pattern="yyyy-mm-dd")
posting_date_winner_a_entry.grid(row=11, column=0, sticky="w", pady=(0, 8))
posting_date_winner_a_entry.set_date(winner_a_default)

ttk.Label(main_frame, text="Publish time option 2a").grid(row=10, column=1, sticky="w", pady=(0, 5))
ttk.Combobox(main_frame, width=4, textvariable=winner_a_hour_var, values=HOUR_OPTIONS, state="readonly").grid(row=11, column=1, sticky="w", pady=(0, 8))
ttk.Combobox(main_frame, width=4, textvariable=winner_a_minute_var, values=MINUTE_OPTIONS, state="readonly").grid(row=11, column=1, sticky="w", padx=(60, 0), pady=(0, 8))

ttk.Label(main_frame, text="Publish date option 2b").grid(row=12, column=0, sticky="w", pady=(0, 5))
posting_date_winner_b_entry = DateEntry(main_frame, width=18, date_pattern="yyyy-mm-dd")
posting_date_winner_b_entry.grid(row=13, column=0, sticky="w", pady=(0, 10))
posting_date_winner_b_entry.set_date(winner_b_default)

ttk.Label(main_frame, text="Publish time option 2b").grid(row=12, column=1, sticky="w", pady=(0, 5))
ttk.Combobox(main_frame, width=4, textvariable=winner_b_hour_var, values=HOUR_OPTIONS, state="readonly").grid(row=13, column=1, sticky="w", pady=(0, 10))
ttk.Combobox(main_frame, width=4, textvariable=winner_b_minute_var, values=MINUTE_OPTIONS, state="readonly").grid(row=13, column=1, sticky="w", padx=(60, 0), pady=(0, 10))

# Right column
ttk.Label(main_frame, text="Hook A").grid(row=0, column=2, sticky="w", padx=(50, 0), pady=(0, 5))
ttk.Combobox(main_frame, width=30, textvariable=hook_a_var, values=HOOK_OPTIONS, state="readonly").grid(row=1, column=2, sticky="w", padx=(50, 0), pady=(0, 10))

ttk.Label(main_frame, text="Hook B").grid(row=2, column=2, sticky="w", padx=(50, 0), pady=(0, 5))
ttk.Combobox(main_frame, width=30, textvariable=hook_b_var, values=HOOK_OPTIONS, state="readonly").grid(row=3, column=2, sticky="w", padx=(50, 0), pady=(0, 10))

ttk.Label(main_frame, text="Moment A").grid(row=4, column=2, sticky="w", padx=(50, 0), pady=(0, 5))
ttk.Combobox(main_frame, width=30, textvariable=moment_a_var, values=MOMENT_OPTIONS, state="readonly").grid(row=5, column=2, sticky="w", padx=(50, 0), pady=(0, 10))

ttk.Label(main_frame, text="Moment B").grid(row=6, column=2, sticky="w", padx=(50, 0), pady=(0, 5))
ttk.Combobox(main_frame, width=30, textvariable=moment_b_var, values=MOMENT_OPTIONS, state="readonly").grid(row=7, column=2, sticky="w", padx=(50, 0), pady=(0, 10))

ttk.Label(main_frame, text="Fixed intervals used").grid(row=8, column=2, sticky="w", padx=(50, 0), pady=(0, 5))
fixed_info = (
    "Create reels after DistroKid: always 1 day\n"
    "Schedule TikTok after reel creation: always 1 day\n"
    "Review items: exactly 24 hours after publish datetime\n"
    "Create second round after review 1b: always 1 day\n"
    "Schedule second round after reel creation: always 1 day\n"
    "Crosspost after review 2b: always 1 day\n"
    "Repost 1 after first crosspost: always 7 days\n"
    "Repost 2 after first crosspost: always 14 days\n"
    "Cleanup after last post: always 7 days"
)
ttk.Label(main_frame, text=fixed_info, justify="left").grid(
    row=9, column=2, rowspan=5, sticky="nw", padx=(50, 0), pady=(0, 10)
)

ttk.Button(main_frame, text="Generate", command=run_tester).grid(row=14, column=0, sticky="w", pady=(0, 15))

ttk.Label(main_frame, text="Result").grid(row=15, column=0, sticky="w")

result_box = tk.Text(main_frame, width=155, height=30, wrap="word")
result_box.grid(row=16, column=0, columnspan=4, sticky="nsew")

scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=result_box.yview)
scrollbar.grid(row=16, column=4, sticky="ns")
result_box.configure(yscrollcommand=scrollbar.set)

root.mainloop()
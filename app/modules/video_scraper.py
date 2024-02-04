import uuid
import json
import yt_dlp
import requests
from datetime import datetime
import time

from modules.image_convert import process_images


def scrape_video():
    json_path = "data/data.json"
    with open(json_path, encoding="utf8") as json_file:
        data = json.load(json_file)

    existing_ids = []

    for item in data["content"]:
        if "youtube_id" in item and item["youtube_id"]:
            existing_ids.append(item["youtube_id"])

    channels = ["@lekkerspelen", "@lekkerspreken"]
    base_url = 'https://www.youtube.com/@/videos'

    delay_seconds = 1
    new_video_count = 0

    for channel in channels:
        url = base_url.replace("@", channel)

        ydl_opts = {
            'skip_download': True,
            'extract_flat': True,
            'youtube_include_dash_manifest': False
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            if 'entries' in info:
                for video in info['entries']:
                    video_id = video.get('id')
                    if not video_id or video_id in existing_ids:
                        continue

                    print(f"\nNieuwe video gevonden: {video.get('title')}\n")

                    video_info = ydl.extract_info(video_id, download=False)

                    video_data = {
                        "id": uuid.uuid4().hex[:4],
                        "type": "video" if channel == "lekkerspelen" else "podcast",
                        "date": datetime.strptime(video_info.get('upload_date'), "%Y%m%d").strftime('%Y-%m-%d'),
                        "title": video.get('title'),
                        "duration": video_info.get('duration'),
                        "youtube_id": video_id,
                    }

                    if channel == "lekkerspelen":
                        activity = input("\nWat is de activitieit van de video?\nGebruik | voor meerdere activiteiten: ")

                        if "|" in activity:
                            activity = activity.split("|")

                        video_data["activity"] = [act.strip() for act in activity]

                    data["content"].append(video_data)

                    time.sleep(delay_seconds)  # Wait before the next request

                    response = requests.get(video_info.get('thumbnail'))
                    process_images(response.content, video_id, "video_youtube")

                    new_video_count += 1
            else:
                print("No videos found")

    with open(json_path, "w", encoding="utf8") as json_file:
        json.dump(data, json_file, indent=4, ensure_ascii=False)

    if new_video_count <= 0:
        print("\nGeen nieuwe video's gevonden.\n")
    else:
        print(f"\n{new_video_count} nieuwe video('s) toegevoegd. Als een video bij een collectie hoort dan moet je dat nog handmatig toevoegen.")

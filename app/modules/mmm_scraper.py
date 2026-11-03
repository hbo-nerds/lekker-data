from modules.mmm_api import mmm
from postgrest.exceptions import APIError
import json
import uuid
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from modules.image_convert import process_images
from pprint import pprint

def scrape_mmm():
    print("- Scrapings from MMM -")

    # get latest twitch_id
    json_path = "data/data.json"
    with open(json_path, encoding="utf8") as json_file:
        data = json.load(json_file)

    content = data["content"]
    twitch_ids = [item for item in content if item.get("twitch_id")]
    latest_video = max(twitch_ids, key=lambda item: int(item["twitch_id"]), default=None)  
    latest_id = latest_video["twitch_id"]

    # fetch missing videos
    try:
        res = (
            mmm.table("videos")
            .select("*, chapters(*, category:categories(*))")
            .gt("video_id", latest_id)
            .order("video_id")
            .execute()
        )
    except APIError as error:
        print(f"Supabase error: {error}")
        return

    # craft new items 
    mmm_data = []

    for video in res.data: 
        item = _build_stream_item(video)
        mmm_data.append(item)

    pprint(mmm_data)

    if len(mmm_data) == 0:
        print("Geen nieuwe streams gevonden")
        return

    mmm_data.reverse()
    
    for content_data in mmm_data:
        while True:
            content_id = uuid.uuid4().hex[:4]
            if content_id not in [item["id"] for item in data["content"]]:
                break

        content_data["id"] = content_id
        content_data["type"] = "stream"
        data["content"].append(content_data)

    with open(json_path, "w", encoding="utf8") as json_file:
        json.dump(data, json_file, indent=4, ensure_ascii=False)

    print("Klaar!")



def _build_stream_item(video):
    # --- STREAM START/END ---
    total_seconds = video["length_sec"]             
    time_start = datetime.fromisoformat(video["recorded_at"])  # parses "+00:00" directly
    time_start = time_start.astimezone(ZoneInfo("Europe/Amsterdam"))
    time_end = time_start + timedelta(seconds=total_seconds)

    # --- STREAM DATE (Amsterdam local date) ---
    date_string = time_start.strftime("%Y-%m-%d")

    # --- STREAM TITLES ---
    titles = [video["title"]]

    # --- GAMES PLAYED ---
    activities = []
    for chapter in video["chapters"]: 
        title = chapter["category"]["title"]
        start = chapter["start_s"]
        end = chapter["end_s"]
        duration = end - start

        activities.append({"title": title, "duration": duration})
 

    # --- THUMBNAIL ---
    twitch_id = video["video_id"]
    thumbnail_url = f"https://backend.malmaarmals.nl/thumbnails/{twitch_id}"  
    response = requests.get(thumbnail_url)
    process_images(response.content, twitch_id, "stream_twitch")

    return {
        "date": date_string,
        "time_start": time_start.strftime("%H:%M:%S"),
        "time_end": time_end.strftime("%H:%M:%S"),
        "titles": titles,
        "activities": activities,
        "duration": total_seconds,
    }


 
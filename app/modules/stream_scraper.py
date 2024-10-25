import os
import re
import time
import uuid
import requests
import json
import yt_dlp
from datetime import datetime, timedelta
from pytz import timezone

from modules.image_convert import process_images

TWITCH_API_ACCESS_TOKEN = os.environ.get('TWITCH_API_ACCESS_TOKEN', '')
TWITCH_API_CLIENT_ID = os.environ.get('TWITCH_API_CLIENT_ID', '')

def scrape_stream():
    print("- Stream -")
    json_path = "data/data.json"
    with open(json_path, encoding="utf8") as json_file:
        data = json.load(json_file)

    twitch_data = _get_streams_from_twitch(data)

    if len(twitch_data) == 0:
        print("Geen nieuwe streams gevonden")
        return
    
    _get_streams_from_youtube(data, twitch_data)

    twitch_data.reverse()

    for content_data in twitch_data:
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

    # -----------------------------

def _get_streams_from_twitch(data):
    print("- Twitch -")
    existing_ids = []

    data["content"].sort(key=_get_datetime_data_item)
    latest = data["content"][-1]
    latest_datetime = _get_datetime_data_item(latest)
    print(f"Zoeken naar streams na laatst bekende stream op {latest_datetime}")

    for item in data["content"]:
        if "twitch_id" in item:
            existing_ids.append(item["twitch_id"])

    authorization_headers = {
        "Authorization": f"Bearer {TWITCH_API_ACCESS_TOKEN}",
        "Client-Id": TWITCH_API_CLIENT_ID
    }

    res = requests.get("https://api.twitch.tv/helix/videos?user_id=52385053&first=100", headers=authorization_headers)
    json_data = res.json()

    if 'status' in json_data and json_data['status'] == 401:
        print('Inloggen mislukt!')
        return []

    twitch_data = []
    archive_ids = []
    highlight_ids = []

    for item in json_data['data']:
        if item['type'] == 'highlight' and item['id'] not in existing_ids:
            highlight_ids.append((item['id'], item))
            continue
        dt = datetime.fromisoformat(item["created_at"].replace("Z", ""))
        if item['type'] == 'archive' and dt >= latest_datetime:
            archive_ids.append((item['id'], item))

    if not archive_ids:
        print("Geen nieuwe streams op Twitch gevonden")
        return twitch_data
    
    print(f"Ik heb {len(archive_ids)} nieuwe streams gevonden op Twitch")

    for id, item in archive_ids:
        title = item["title"]
        print(f"\nStream {id} met titel: {title}")
        stream_item = _build_stream_item(item)
        if stream_item:
            twitch_data.append(stream_item)

    for id, item in highlight_ids:
        title = item["title"]
        corresponding = [item for item in twitch_data if item['titles'][0] == title]
        if len(corresponding) == 1:
            corresponding[0]['twitch_id'] = item['id']
            print(f'Match higlight en stream met title: {title}')

    return twitch_data

    # -----------------------------

def _get_datetime_data_item(item):
    if 'time_start' not in item and 'date' not in item:
        return datetime(1970, 1, 1, 0, 0, 0)
    if 'time_start' not in item: 
        return datetime.strptime(item["date"], "%Y-%m-%d")
    
    return datetime.strptime(item["date"] + " " + item["time_start"], "%Y-%m-%d %H:%M:%S")

    # -----------------------------

def _build_stream_item(item):
    # --- STREAM DURATION ---
    duration_string = item["duration"]
    total_seconds = _get_seconds_form_duration_string(duration_string)

    if total_seconds < 60 * 60:
        print(f"Deze stream duurt minder dan een uur. Overslaan?")
        answer = input("Ja/Nee: ").lower()
        if answer[:1] == "j":
            return None
    
    # --- STREAM DATE ---
    date_string = item["created_at"].split("T")[0]

    # --- STREAM START/END ---
    # set time start and time end based on created_at and duration
    time_start = datetime.fromisoformat(item["created_at"].replace("Z", "") + "+00:00")
    time_start = time_start.astimezone(timezone('Europe/Amsterdam'))
    time_end = time_start + timedelta(0, total_seconds)

    # --- STREAM TITLES ---
    titles = [item['title']]
    while True:
        print("Voer een extra titel in. Wil je verder gaan? Druk dan op enter.")
        title = input("Titel: ") 
        
        if not title:
            break
        titles.append(title)

    # --- GAMES PLAYED ---
    activities = []
    while True:
        print("Voer een activiteit in. Wil je verder gaan? Druk dan op enter.")
        title = input("Titel: ") 
        if not title:
            break

        while True:
            try:
                duration = int(input("Duur (in seconden): "))
                break
            except:
                print('Ongeldige duur, probeer het nog eens.')
                continue
        
        activities.append({"title": title, "duration": duration})

    # --- THUMBNAILS ---
    twitch_id = item["id"]
    thumbnail = item['thumbnail_url'].replace("%{width}x%{height}",  "640x360")
    response = requests.get(thumbnail)
    process_images(response.content, twitch_id, "stream_twitch")

    data = {
        "date": date_string,
        "time_start": time_start.strftime("%H:%M:%S"),
        "time_end": time_end.strftime("%H:%M:%S"),
        "titles": titles,
        "activities": activities,
        "duration": total_seconds,
    }

    return data

    # -----------------------------

ISO_DURATION_RE = re.compile(r'^((\d+)h)?((\d+)m)?((\d+)s)?$', re.I)
def _get_seconds_form_duration_string(duration_string):
    match = ISO_DURATION_RE.match(duration_string)
    
    hours = int(match.group(2) or 0)
    minutes = int(match.group(4) or 0)
    seconds = int(match.group(6) or 0)
    
    return hours * 3600 + minutes * 60 + seconds


def _get_streams_from_youtube(data, twitch_data):
    print("\n\n- Youtube -")

    streams = []

    ydl_opts = {
        'skip_download': True,
        'extract_flat': True,
        'youtube_include_dash_manifest': False,
    }
   
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # get streams from playlist "Lekker spelen live streams (VOD)"
        info = ydl.extract_info("https://www.youtube.com/playlist?list=PL_y_qOVNZ5i8UUv9Tg_pMd9RSqO9pNzdi", download=False, process=False)
        
        if 'entries' in info:
            for stream in info['entries']:
                streams.append(stream)

    new_streams = [] 

    for i, t in enumerate(twitch_data):
        new_streams.append(streams[i])
        yt_id = streams[i]["id"]
        yt_title = streams[i]["title"]
        twitch_id = t["twitch_id"] if "twitch_id" in t else ""
        twitch_title = t["titles"][0]
        print("\nVolgende Youtube - Twitch koppeling gemaakt:")
        print(f"Youtube stream: ({yt_id}) {yt_title}")
        print(f"Twitch stream: ({twitch_id}) {twitch_title}")
        t["youtube_id"] = yt_id

    print("\nControleer bovenstaande koppelingen goed!")

    # Get Thumbnails
    for stream in new_streams:
        url = stream["thumbnails"][-1]['url'].replace("hqdefault", "maxresdefault")
        response = requests.get(url)
        process_images(response.content, stream["id"], "stream_youtube")

    # -----------------------------

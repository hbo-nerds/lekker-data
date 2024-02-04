import uuid
import json
import yt_dlp
import requests
from datetime import datetime

from modules.image_convert import process_images


def scrape_third_party_video():
    json_path = "data/data.json"
    with open(json_path, encoding="utf8") as json_file:
        data = json.load(json_file)

    existing_ids = []

    for item in data["content"]:
        if "youtube_id" in item and item["youtube_id"]:
            existing_ids.append(item["youtube_id"])

    url = input("Wat is de URL van de video?: ")

    if "youtu.be" not in url and "youtube.com" not in url:
        print("Dit is geen geldige Youtube URL.")
        return

    ydl_opts = {
        'skip_download': True,
        'extract_flat': True,
        'youtube_include_dash_manifest': False
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        video_info = ydl.extract_info(url, download=False)
        video_id = video_info.get('id')

        if not video_id or video_id in existing_ids:
            print("Deze video is al toegevoegd.")

        video_data = {
            "id": uuid.uuid4().hex[:4],
            "title": video_info.get('title'),
            "duration": video_info.get('duration'),
            "youtube_id": video_id,
        }

        while True:
            content_type_id = input("\nWat voor soort video is dit?\n1. Stream\n2. Video\n3. Podcast\nMaak een keuze: ")

            if content_type_id == "1":
                content_type = "stream"
                video_data["type"] = "stream"
                break
            elif content_type_id == "2":
                content_type = "video"
                video_data["type"] = "video"
                break
            elif content_type_id == "3":
                content_type = "podcast"
                video_data["type"] = "podcast"
                break
            else:
                print("Dat is geen optie lekkerKoppie. Probeer het opnieuw.")

        date_og = datetime.strptime(video_info.get('upload_date'), "%Y%m%d").strftime('%Y-%m-%d')
        og_stream = None

        if content_type == "stream":
            twitchtracker_id = input("\nWat is de TwitchTracker ID van de stream? (Laat leeg als deze niet bestaat): ")
            if twitchtracker_id:
                for item in data["content"]:
                    if item.get("twitchtracker_id") == twitchtracker_id:
                        og_stream = item
                    
                if not og_stream:
                    print("Er is geen stream gevonden met deze TwitchTracker ID.")
                    return
                
            if og_stream:
                if og_stream.get("twitch_id") or og_stream.get("youtube_id"):
                    print("Er bestaat nog een originele Twitch of Youtube video van deze stream. Voeg je url handmatig toe.")
                    return
            
                video_data = og_stream
                video_data["youtube_id"] = video_id


        if not og_stream:
            while True:
                date = input(f"\nWat is de datum van de originele {content_type}? (YYYY-MM-DD)\nLaat leeg als je de datum van de video wilt gebruiken ({date_og}):")

                if not date:
                    video_data["date"] = date_og
                    break
                else:
                    try:
                        datetime.strptime(date, "%Y-%m-%d")
                        video_data["date"] = date
                        break
                    except ValueError:
                        print("Dat is geen geldige datum lekkerKoppie. Gebruik het formaat (YYYY-MM-DD). Probeer het opnieuw.")

            if content_type != "podcast":
                activity = input("\nWat is de activitieit van de video?\nGebruik | voor meerdere activiteiten: ")

                if "|" in activity:
                    activity = [act.strip() for act in  activity.split("|")]
                    video_data["activity"] = activity

                if content_type == "stream":
                    del video_data["activity"]
                    activity = [activity] if not isinstance(activity, list) else activity
                    if len(activity) == 1:
                        video_data["activities"] = [{"title": activity[0], "duration": video_data["duration"]}]
                    else:
                        video_data["activities"] = []
                        activity_duration_sum = 0
                        success = False
                        while not success:
                            for i, act in enumerate(activity):
                                while True:
                                    duration = input(f"Hoelang duurde de activiteit '{act}'? (in seconden): ")
                                    if duration.isdigit() and int(duration) > 0 and int(duration):
                                        video_data["activities"].append({"title": act, "duration": int(duration)})
                                        break
                                    else:
                                        print("Dat is geen geldige duur lekkerKoppie. Geef gewoon het aantal seconden op. Probeer het opnieuw.")

                                activity_duration_sum += int(duration)

                                if i == len(activity) - 2:
                                    if activity_duration_sum > video_data["duration"]:
                                        print("De totale duur van de activiteiten is langer dan de video. Probeer het opnieuw.")
                                        video_data["activities"] = []
                                        activity_duration_sum = 0
                                        break
                                    
                                    # Add remaining duration to last activity
                                    video_data["activities"].append({
                                        "title": activity[-1],
                                        "duration": video_data["duration"] - activity_duration_sum
                                    })

                                    success = True
                                    break

        if not og_stream:
            data["content"].append(video_data)

        response = requests.get(video_info.get('thumbnail'))
        process_images(response.content, video_id, "video_youtube")

        with open(json_path, "w", encoding="utf8") as json_file:
            json.dump(data, json_file, indent=4, ensure_ascii=False)

        print("\nDe video is toegevoegd aan de database. Overige aanpassingen mogen handmatig gedaan worden.")
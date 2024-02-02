import uuid
import requests
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC

from modules.image_convert import process_images


def scrape_stream():
    json_path = "data/data.json"
    with open(json_path, encoding="utf8") as json_file:
        data = json.load(json_file)

    use_profile = False

    while True:
        print(
            "\nHet kan zijn dat TwitchTracker je niet doorlaat zonder Chrome profiel (Verify that you are human)."
        )

        answer = input("Wil je je eigen Chrome profiel gebruiken? (y/n)")

        if answer.lower() == "y":
            use_profile = True
            break
        elif answer.lower() == "n":
            break
        else:
            print("Dat is geen optie. Probeer het opnieuw.")

    if use_profile:
        # Path to your Chrome profile
        profile_path = "C:/Users/danie/AppData/Local/Google/Chrome/User Data"

        options = Options()
        options.add_argument(f"user-data-dir={profile_path}")

        # Ensure you replace 'Default' with the appropriate profile name if necessary
        options.add_argument("profile-directory=Default")

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=options
        )
    else:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    tt_data = _scrape_twitch_tracker(data, driver)

    if len(tt_data) == 0:
        print("Geen nieuwe streams gevonden")
        driver.quit()
        return

    _scrape_twitch(data, driver, tt_data)

    _scrape_youtube(data, driver, tt_data)

    driver.quit()

    for content_data in tt_data:
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


def _scrape_twitch_tracker(data, driver):
    existing_ids = []

    for item in data["content"]:
        if "twitchtracker_id" in item:
            existing_ids.append(item["twitchtracker_id"])

    # Get TwitchTracker data
    driver.get("https://twitchtracker.com/lekkerspelen/streams")
    streams = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "streams"))
    )

    tt_data = []

    # Find multiple by selector
    tt_a_elements = streams.find_elements(By.CSS_SELECTOR, "tbody > tr > td > a")

    urls = []

    for a_element in tt_a_elements:
        url = a_element.get_attribute("href")
        tt_id = url.split("/")[-1]
        if tt_id not in existing_ids:
            urls.append((url, tt_id))

    if not urls:
        print("Geen nieuwe streams op TwitchTracker gevonden")
        return tt_data

    for url, tt_id in urls:
        tt_data.append(_scrape_twitch_tracker_page(driver, url, tt_id))

    return tt_data


def _scrape_twitch_tracker_page(driver, url, tt_id):
    driver.get(url)

    stream_duration_text = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[contains(text(), 'Stream Duration')]")
        )
    )

    # --- STREAM DURATION ---
    parent_element = stream_duration_text.find_element(By.XPATH, "..")
    first_child = parent_element.find_element(By.XPATH, "*")
    inner_text = first_child.get_attribute("innerText")
    hours = int(inner_text.split("h")[0] or "0")
    minutes = int(inner_text.split("h")[1].split("m")[0] or "0")
    total_seconds = (hours * 60 + minutes) * 60
    # -----------------------

    driver.implicitly_wait(5)

    # --- STREAM DATE ---
    date = driver.find_element(by=By.ID, value="stream-date").get_attribute("innerText")

    # Convert DECEMBER 12, 2016 to proper date time
    date = datetime.strptime(date, "%B %d, %Y")
    # -------------------

    # --- STREAM START/END ---
    timestamp_elements = driver.find_elements(By.CLASS_NAME, "stream-timestamp-dt")
    time_start = timestamp_elements[0].get_attribute("innerText")
    time_end = timestamp_elements[1].get_attribute("innerText")

    # Convert Mon, Aug 7, 20:32 to proper date time
    time_start = datetime.strptime(time_start, "%a, %b %d, %H:%M")
    time_end = datetime.strptime(time_end, "%a, %b %d, %H:%M")

    # Add year from date to time_start and time_end
    time_start = time_start.replace(year=date.year)
    time_end = time_end.replace(year=date.year)
    # -----------------------

    # --- GAMES PLAYED ---
    card_title_elements = driver.find_elements(By.CLASS_NAME, "card-title")
    card_titles = [
        element.get_attribute("innerText") for element in card_title_elements
    ]

    card_duration_elements = driver.find_elements(By.CLASS_NAME, "stats-duration")
    card_durations = [
        element.get_attribute("innerText") for element in card_duration_elements
    ]

    activities = []
    for j, title in enumerate(card_titles):
        duration = card_durations[j]
        hours = int(duration.split("h")[0] or "0")
        minutes = int(duration.split("h")[1].split("m")[0] or "0")
        total_seconds_game = (hours * 60 + minutes) * 60
        activities.append({"title": title, "duration": total_seconds_game})

    # --- STREAM TITLES ---
    stream_title_element = driver.find_elements(By.ID, "stream-titles")

    if len(stream_title_element) > 0:
        # Find all child elements with class 'line' inside 'stream-title'
        line_elements = stream_title_element[0].find_elements(By.CLASS_NAME, "line")

        # Extract the 'innerText' of each 'line' element
        titles = [element.get_attribute("innerText")[6::] for element in line_elements]
    else:
        titles = ["Lekker '" + card_titles[0] + "' spelen"]
    # ---------------------

    data = {
        "twitchtracker_id": tt_id,
        "date": date.strftime("%Y-%m-%d"),
        "time_start": time_start.strftime("%H:%M"),
        "time_end": time_end.strftime("%H:%M"),
        "titles": titles,
        "activities": activities,
        "duration": total_seconds,
    }

    return data


def _scrape_twitch(data, driver, tt_data):
    driver.get("https://www.twitch.tv/lekkerspelen/videos?filter=highlights&sort=time")

    streams = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located(
            (By.XPATH, "//a[@data-a-target='preview-card-image-link']")
        )
    )

    existing_ids = []

    for item in data["content"]:
        if "twitch_id" in item and item["twitch_id"]:
            existing_ids.append(item["twitch_id"])

    new_streams = []
    new_ids = []

    for stream in streams:
        twitch_id = stream.get_attribute("href").split("/")[-1].split("?")[0]
        if twitch_id not in existing_ids:
            new_ids.append(twitch_id)
            new_streams.append(stream)

    if not new_streams:
        print("Geen nieuwe highlights op Twitch gevonden")
        return

    print(f"Ik heb {len(new_streams)} nieuwe highlights gevonden")

    print(
        """Ik ga ervan uit dat de nieuwste streams gelinkt zijn aan de nieuwste highlights.
Pas het handmatig aan als dit niet klopt."""
    )

    for i, tt in enumerate(tt_data):
        tt["twitch_id"] = new_ids[i]

    # Get Twitch data
    thumbnails = []

    for stream in new_streams:
        # Find xpath div div div div div img
        thumbnail = stream.find_element(By.XPATH, ".//div/div/div/div/div/img")
        thumbnails.append(thumbnail.get_attribute("src").replace("320x180", "640x360"))

    # Download all the thumbnails using requests
    for i, thumbnail in enumerate(thumbnails):
        response = requests.get(thumbnail)
        process_images(response.content, tt_data[i]["twitchtracker_id"], "twitch")


def _scrape_youtube(data, driver, tt_data):
    driver.get("https://www.youtube.com/@lekkerspelen/streams")

    page = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (
                By.CSS_SELECTOR,
                "ytd-two-column-browse-results-renderer[page-subtype='channels']",
            )
        )
    )

    streams = page.find_elements(
        By.CSS_SELECTOR, "a.yt-simple-endpoint.style-scope.ytd-thumbnail"
    )

    existing_ids = []

    for item in data["content"]:
        if "youtube_id" in item and item["youtube_id"]:
            existing_ids.append(item["youtube_id"])

    new_streams = []
    new_ids = []

    print("existing ids count", len(existing_ids))

    for stream in streams:
        yt_id = stream.get_attribute("href").split("=")[1].split("&")[0]
        if yt_id not in existing_ids:
            print(yt_id)
            new_ids.append(yt_id)
            new_streams.append(stream)

    if not new_streams:
        print("Geen nieuwe streams op Youtube gevonden")
        return

    print(f"Ik heb {len(new_streams)} nieuwe Youtube stream(s) gevonden")

    print(
        """Ik ga ervan uit dat de nieuwste streams op TwitchTracker gelinkt zijn aan de nieuwste streams op Youtube.
Pas het handmatig aan als dit niet klopt."""
    )

    for i, tt in enumerate(tt_data):
        tt["youtube_id"] = new_ids[i]

    # Get Twitch data
    thumbnails = []

    for stream in new_streams:
        thumbnail = stream.find_element(By.CSS_SELECTOR, "img")
        if thumbnail:
            src = thumbnail.get_attribute("src")
            if src:
                thumbnails.append(src.replace("hqdefault", "maxresdefault"))

    # Download all the thumbnails using requests
    for i, thumbnail in enumerate(thumbnails):
        response = requests.get(thumbnail)
        process_images(response.content, new_ids[i], "youtube")

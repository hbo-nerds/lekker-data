from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
import subprocess
import json
from bs4 import BeautifulSoup


def edit_content():
    while True:
        issue = input("\nWat is het issue nummer?: ")

        # Check if issue is a positive integer
        if not issue.isdigit() or int(issue) < 1:
            print("Dat is geen geldig issue nummer lekkerKoppie. Probeer het opnieuw.")
        else:
            break

    issue = int(issue)

    options = Options()
    options.add_argument("--headless")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )

    driver.get(f"https://github.com/lekkersicko/lekker-data/issues/{issue}")

    title = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, ".js-issue-title.markdown-title")
        )
    )

    content_id = title.text.replace("[Submission]", "").strip()

    # Use beautifulsoup to parse the html
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    description_element = soup.find("h3", text="Beschrijving").find_next_sibling("p")
    if description_element:
        description = description_element.text

    tags_element = soup.find("h3", text="Tags").find_next_sibling("p")

    if tags_element:
        tags = tags_element.text.split(",")
        for i, tag in enumerate(tags):
            tags[i] = tag.strip()

    json_path = "data/data.json"
    with open(json_path, encoding="utf8") as json_file:
        full_data = json.load(json_file)
        data = full_data["content"]

    # Find data with the same content_id
    success = False
    for i, item in enumerate(data):
        if item["id"] == content_id:
            if description:
                if "description" in data[i] and data[i]["description"]:
                    while True:
                        print(
                            "Deze content heeft al een beschrijving. Wil je deze overschrijven?"
                        )
                        print(f"Oude beschrijving:\n\n{data[i]['description']}\n\n")
                        answer = input("Overschrijven? (y/n): ")
                        if answer.lower() != "y":
                            print("Beschrijving niet overschreven.")
                            break
                        elif answer.lower() == "y":
                            data[i]["description"] = description
                            success = True
                            break
                        else:
                            print(
                                "Dat is geen optie lekkerKoppie. Probeer het opnieuw."
                            )
                else:
                    data[i]["description"] = description
                    success = True

            if tags:
                if "tags" in data[i] and data[i]["tags"]:
                    while True:
                        print(
                            "Deze content heeft al tags. Wil je de tags overschrijven of toevoegen?"
                        )
                        print(f"Oude tags: \n\n{', '.join(data[i]['tags'])}\n\n")

                        print("1. Overschrijven")
                        print("2. Toevoegen")
                        print("3. Overslaan")

                        answer = input("Maak een keuze: ")

                        if answer == "1":
                            data[i]["tags"] = tags
                            success = True
                            break
                        elif answer == "2":
                            data[i]["tags"].extend(tags)
                            # Remove duplicates
                            data[i]["tags"] = list(set(data[i]["tags"]))
                            success = True
                            break
                        elif answer == "3":
                            print("Tags niet aangepast.")
                            break
                        else:
                            print(
                                "Dat is geen optie lekkerKoppie. Probeer het opnieuw."
                            )

                else:
                    data[i]["tags"] = tags
                    success = True
    if not success:
        print("Content niet aangepast. Sluit de issue indien nodig.")
        return

    full_data["content"] = data

    with open(json_path, "w", encoding="utf8") as json_file:
        json.dump(full_data, json_file, ensure_ascii=False, indent=4)

    print("Content aangepast.")

    while True:
        answer = input("\nWil je de aanpassingen gelijk committen? (y/n): ")
        if answer.lower() == "y":
            break
        elif answer.lower() == "n":
            print("Aanpassingen niet gecommit.")
            return
        else:
            print("Dat is geen optie lekkerKoppie. Probeer het opnieuw.")

    subprocess.run(["git", "pull"], check=True)
    subprocess.run(["git", "add", json_path], check=True)
    subprocess.run(
        ["git", "commit", "-m", f"Update content {content_id} (Resolves #{issue})"],
        check=True,
    )

    print("Aanpassingen gecommit.")

    while True:
        answer = input("\nWil je de aanpassingen ook pushen? (y/n): ")
        if answer.lower() == "y":
            break
        elif answer.lower() == "n":
            print("Aanpassingen niet gepushed.")
            return
        else:
            print("Dat is geen optie lekkerKoppie. Probeer het opnieuw.")

    subprocess.run(["git", "push"], check=True)
    print("Aanpassingen gepushed.")
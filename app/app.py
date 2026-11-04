from dotenv import load_dotenv
load_dotenv()

from modules.stream_scraper import scrape_stream
from modules.video_scraper import scrape_video
from modules.video_scraper_third_party import scrape_third_party_video
from modules.content_editor import edit_content
from modules.mmm_scraper import scrape_mmm


def main():
    while True:
        print("\nWelkom bij Lekker Data. Wat wil je doen?")
        print("1. Nieuwste stream(s) toevoegen via Twitch")
        print("2. Nieuwste stream(s) toevoegen via malmaarmals")
        print("3. Nieuwste video(s) toevoegen")
        print("4. 3rd-party video toevoegen")
        print("5. Content aanpassen")
        # print("6. Een thumbnail downloaden")
        print("7. Exit")

        choice = input("Maak een keuze: ")

        if choice == "1":
            scrape_stream()
        elif choice == "2":
            scrape_mmm()
        elif choice == "3":
            scrape_video()
        elif choice == "4":
            scrape_third_party_video()
        elif choice == "5":
            edit_content()
        elif choice == "7":
            print("lekkerDag lekkerLief")
            break
        else:
            print("Dat is geen optie lekkerKoppie. Probeer het opnieuw.")


if __name__ == "__main__":
    main()

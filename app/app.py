from modules.stream_scraper import scrape_stream


def main():
    while True:
        print("\nWelkom bij Lekker Data. Wat wil je doen?")
        print("1. Nieuwste stream(s) toevoegen")
        print("2. Nieuwste video(s) toevoegen")
        print("3. 3rd-party video toevoegen")
        print("4. Een video aanpassen")
        print("5. Een thumbnail downloaden")
        print("6. Exit")

        choice = input("Maak een keuze: ")

        if choice == "1":
            scrape_stream()
        elif choice == "2":
            pass
            # feature2()
        elif choice == "6":
            print("lekkerDag lekkerLief")
            break
        else:
            print("Dat is geen optie lekkerKoppie. Probeer het opnieuw.")


if __name__ == "__main__":
    main()

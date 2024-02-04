# Lekker Data

Dataverzameling van Lekker Spelen content.

## JSON 🎈

Alle data wordt opgeslagen in één grote JSON. Deze kan je vinden in `data/data.json`.

De JSON bevat een `content` en `collections` object. In collections staat informatie over de series. Content die met elkaar te maken heeft.

Let er op dat velden die `null` zijn niet aanwezig hoeven te zijn in de JSON.

Dit zijn de velden die je in de objecten van `content` vindt:

### Standaard velden

* `"id": string` - De ID van de content. Dit is een hex string van 4 karakters.
* `"type": string` - Het type van de content. Dit kan zijn: `"video"`, `"stream"`, `"podcast"`
* `"date": string` - De datum dat de content is geupload of gestreamd. In het formaat `YYYY-MM-DD`
* `"duration": integer` - De lengte van de content duurt in seconden.
* `"youtube_id": string?` - De ID van de YouTube video. Dit is de ID die je in de URL van de video vindt. Bijvoorbeeld: `"dQw4w9WgXcQ"`
* `"description": string?` - De beschrijving van de content.
* `"collection": integer?` - De ID van de collection waar de content bij hoort. Dit is een hex string van 4 karakters.

### Exclusieve velden


#### Video/Podcast

Voor de objecten waarbij `type == "video"` of `type == "podcast"`:

* `"title": string` - De titel van de content. Bijvoorbeeld `"Lekker Spelen: The Lion King - Deel 1"`

#### Video

Voor de objecten waarbij `type == "video"`:

* `"activity": string|string[]` - De activiteit van de content. Bijvoorbeeld `"Drawing from Memory"` of `["The Lion King", "Drawing from Memory"]`

#### Stream

Voor de objecten waarbij `type == "stream"`:

* `"titles": string[]` - Een lijst van alle titels die de stream heeft gehad. Bijvoorbeeld: `["100 RONDJES in VR EFTELING ACHTBAAN"]`
* `title_main: int?` - De index van de titel in de `titles` lijst die als hoofdtitel van de stream wordt gezien.
* `title_custom: string?` - Een zelfbedachte titel voor als de stream geen goede titels heeft die de stream omschrijft.
* `"activities": string[]` - Een lijst van alle activiteiten die zijn gedaan tijdens deze stream. Bijvoorbeeld: `["Drawing from Memory"]`
* `"twitchtracker_id": string?` - De ID van de stream op TwitchTracker. Niet beschikbaar voor streams voor 21 november 2016.
* `"twitch_id": string?` - De ID van de stream op Twitch.
* `"extra_urls: object[]?` - Een lijst van extra URLs die bij de stream horen. Bijvoorbeeld: `[{ "title": "Deel 2", url: "https://www.twitch.tv/videos/123456789"]`
* `"tags": string[]?` - De tags die bij de stream horen. Bijvoorbeeld: `["tekenen", "peter vs timon"]`
* `"time_start": string?` - De tijd dat de stream begon. In het formaat `HH:MM`.
* `"time_end": string?` - De tijd dat de stream eindigde. In het formaat `HH:MM`.
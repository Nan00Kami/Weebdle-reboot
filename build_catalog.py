import json
import time
import requests

BASE_URL = "https://api.jikan.moe/v4"
TARGET_COUNT = 600  # High-impact roster size (Top 600 characters)
OUTPUT_FILE = "characters.json"

catalog = []
anime_cache = {}

def fetch(url):
    while True:
        try:
            res = requests.get(url, timeout=12)
            if res.status_code == 429:
                time.sleep(4)
                continue
            if res.status_code != 200:
                return None
            return res.json()
        except Exception:
            time.sleep(2)

page = 1
print(f"Fetching top {TARGET_COUNT} popular MAL characters...")

while len(catalog) < TARGET_COUNT:
    page_data = fetch(f"{BASE_URL}/characters?page={page}&order_by=favorites&sort=desc")
    if not page_data or not page_data.get("data"):
        break

    for item in page_data["data"]:
        if len(catalog) >= TARGET_COUNT:
            break

        char_id = item.get("mal_id")
        char_name = item.get("name")
        image_url = item.get("images", {}).get("jpg", {}).get("image_url", "")

        time.sleep(0.35)
        details = fetch(f"{BASE_URL}/characters/{char_id}/full")
        if not details or not details.get("data"):
            continue

        anime_list = details["data"].get("anime", [])
        if not anime_list:
            continue

        primary_anime = anime_list[0].get("anime", {})
        anime_id = str(primary_anime.get("mal_id"))
        anime_title = primary_anime.get("title")

        if anime_id not in anime_cache:
            time.sleep(0.35)
            a_data = fetch(f"{BASE_URL}/anime/{anime_id}")
            if a_data and a_data.get("data"):
                meta = a_data["data"]
                year = meta.get("year") or meta.get("aired", {}).get("prop", {}).get("from", {}).get("year") or "N/A"
                genres = [g.get("name") for g in meta.get("genres", [])]
                demos = [d.get("name") for d in meta.get("demographics", [])]
                themes = [t.get("name") for t in meta.get("themes", [])]

                anime_cache[anime_id] = {
                    "anime": anime_title,
                    "year": year,
                    "genre": genres[0] if genres else "Unknown",
                    "demographic": demos[0] if demos else "None",
                    "theme": themes[0] if themes else "None"
                }
            else:
                anime_cache[anime_id] = {
                    "anime": anime_title, "year": "N/A", "genre": "Unknown", "demographic": "None", "theme": "None"
                }

        anime_meta = anime_cache[anime_id]

        entry = {
            "name": char_name,
            "image": image_url,
            "anime": anime_meta["anime"],
            "year": anime_meta["year"],
            "gender": "Unknown",
            "genre": anime_meta["genre"],
            "demographic": anime_meta["demographic"],
            "theme": anime_meta["theme"]
        }

        catalog.append(entry)
        print(f"[{len(catalog)}/{TARGET_COUNT}] {char_name} ({anime_title})")

    page += 1

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(catalog, f, ensure_ascii=False, indent=2)

print("Database generation complete!")

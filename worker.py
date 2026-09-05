import os
import sys
import time
import json
import requests

# ----------------- CONFIGURATION PER DEVICE -----------------
START_PAGE = 1       # Change to 101 on device 2, 201 on device 3, etc.
END_PAGE = 100       # Change to 200 on device 2, 300 on device 3, etc.
MIN_FAVORITES = 30   # Cuts off obscure characters like Blei completely
DEVICE_ID = "dev1"   # Output file identifier (e.g. dev1, dev2, dev3)
# -------------------------------------------------------------

BASE_URL = "https://api.jikan.moe/v4"
OUTPUT_FILE = f"scraped_part_{DEVICE_ID}.json"
ANIME_CACHE_FILE = f"anime_cache_{DEVICE_ID}.json"

anime_cache = {}
if os.path.exists(ANIME_CACHE_FILE):
    with open(ANIME_CACHE_FILE, "r", encoding="utf-8") as f:
        anime_cache = json.load(f)

extracted_characters = []

def safe_req(url):
    while True:
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 429:
                time.sleep(3.5)
                continue
            if r.status_code != 200:
                return None
            return r.json()
        except Exception:
            time.sleep(2)

print(f"[{DEVICE_ID}] Scraping pages {START_PAGE} to {END_PAGE} (Min Favorites: {MIN_FAVORITES})...")

stop_scraping = False

for page in range(START_PAGE, END_PAGE + 1):
    if stop_scraping:
        break

    list_data = safe_req(f"{BASE_URL}/characters?page={page}&order_by=favorites&sort=desc")
    if not list_data or not list_data.get("data"):
        break

    for char in list_data["data"]:
        favs = char.get("favorites", 0)
        
        # Immediate skip: saves downstream API calls
        if favs < MIN_FAVORITES:
            print(f"Reached cutoff limit ({favs} favorites). Stopping device.")
            stop_scraping = True
            break

        char_id = char.get("mal_id")
        char_name = char.get("name")
        image_url = char.get("images", {}).get("jpg", {}).get("image_url", "")

        time.sleep(0.35)
        char_detail = safe_req(f"{BASE_URL}/characters/{char_id}/full")
        if not char_detail or not char_detail.get("data"):
            continue

        anime_roles = char_detail["data"].get("anime", [])
        if not anime_roles:
            continue

        # Get parent anime metadata
        primary_anime = anime_roles[0].get("anime", {})
        anime_id = str(primary_anime.get("mal_id"))
        anime_title = primary_anime.get("title")

        if anime_id not in anime_cache:
            time.sleep(0.35)
            a_res = safe_req(f"{BASE_URL}/anime/{anime_id}")
            if a_res and a_res.get("data"):
                ad = a_res["data"]
                year = ad.get("year") or ad.get("aired", {}).get("prop", {}).get("from", {}).get("year") or "N/A"
                genres = [g.get("name") for g in ad.get("genres", [])]
                demos = [d.get("name") for d in ad.get("demographics", [])]
                themes = [t.get("name") for t in ad.get("themes", [])]

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

        anime_info = anime_cache[anime_id]

        extracted_characters.append({
            "name": char_name,
            "image": image_url,
            "anime": anime_info["anime"],
            "year": anime_info["year"],
            "gender": "Unknown",
            "genre": anime_info["genre"],
            "demographic": anime_info["demographic"],
            "theme": anime_info["theme"],
            "favorites": favs
        })
        print(f"[{DEVICE_ID}] Saved: {char_name} (★ {favs})")

    # Save checkpoints
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(extracted_characters, f, ensure_ascii=False, indent=2)
    with open(ANIME_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(anime_cache, f, ensure_ascii=False)

print(f"[{DEVICE_ID}] Finished batch! Total items: {len(extracted_characters)}")

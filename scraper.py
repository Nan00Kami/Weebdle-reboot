import json
import time
import sys
from datetime import datetime
import requests

BASE_URL = "https://jikan.moe"

def get_top_popular_anime(limit=100):
    """Fetches the top popular anime within the specified date range."""
    anime_list = []
    page = 1
    
    # Target range constraints
    START_DATE = datetime(2010, 1, 1)
    END_DATE = datetime(2026, 9, 30)
    
    print("Fetching top popular anime...")
    
    while len(anime_list) < limit:
        # Order by popularity to grab the most popular ones first
        url = f"{BASE_URL}/anime?order_by=popularity&sort=asc&page={page}"
        try:
            response = requests.get(url)
            if response.status_code == 429:
                print("Rate limited! Sleeping for 5 seconds...")
                time.sleep(5)
                continue
                
            response.raise_for_status()
            data = response.json().get("data", [])
            
            if not data:
                break  # End of data catalog
                
            for item in data:
                if len(anime_list) >= limit:
                    break
                    
                # Parse broadcast date strings safely
                from_date_str = item.get("aired", {}).get("from")
                if from_date_str:
                    try:
                        # Jikan dates typically follow ISO 8601 substring formats
                        aired_date = datetime.fromisoformat(from_date_str.split("T")[0])
                        if START_DATE <= aired_date <= END_DATE:
                            anime_list.append({
                                "id": item["mal_id"],
                                "title": item["title"]
                            })
                    except ValueError:
                        continue # Skip if date can't be parsed
                        
            print(f"Collected {len(anime_list)}/100 valid anime entries...")
            page += 1
            time.sleep(1.5)  # Respect API rate limits
            
        except Exception as e:
            print(f"Error fetching anime list: {e}")
            sys.exit(1)
            
    return anime_list[:limit]

def get_characters_for_anime(anime_id):
    """Fetches character data for a given anime ID."""
    url = f"{BASE_URL}/anime/{anime_id}/characters"
    try:
        response = requests.get(url)
        if response.status_code == 429:
            time.sleep(4)
            return get_characters_for_anime(anime_id) # Retry on rate limit
            
        if response.status_code != 200:
            return []
            
        characters_data = response.json().get("data", [])
        extracted = []
        
        for item in characters_data:
            char = item.get("character", {})
            extracted.append({
                "name": char.get("name"),
                "image_url": char.get("images", {}).get("jpg", {}).get("image_url"),
                "role": item.get("role")  # E.g., Main, Supporting
            })
        return extracted
    except Exception:
        return []

def main():
    target_anime = get_top_popular_anime(100)
    output_data = []
    
    print("\nStarting character data extraction...")
    for idx, anime in enumerate(target_anime):
        print(f"[{idx+1}/100] Scraping characters for: {anime['title']}")
        characters = get_characters_for_anime(anime["id"])
        
        output_data.append({
            "anime_title": anime["title"],
            "anime_mal_id": anime["id"],
            "characters": characters
        })
        time.sleep(1.5)  # Enforce pause to bypass rate limiter
        
    # Save results to disk
    with open("mal_characters.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=4, ensure_ascii=False)
        
    print("\nScraping complete! Saved to 'mal_characters.json'")

if __name__ == "__main__":
    main()

import os
import glob
import json
import hashlib

DATA_DIR = "data"
CHUNKS_DIR = os.path.join(DATA_DIR, "chunks")
INDEX_PATH = os.path.join(DATA_DIR, "search_index.json")

os.makedirs(CHUNKS_DIR, exist_ok=True)

all_characters = {}
part_files = glob.glob("scraped_part_*.json")

print(f"Found {len(part_files)} device output files. Merging...")

for file_path in part_files:
    with open(file_path, "r", encoding="utf-8") as f:
        entries = json.load(f)
        for item in entries:
            # Deduplicate by character name
            all_characters[item["name"]] = item

print(f"Total unique characters across all devices: {len(all_characters)}")

# Partition into 256 hash chunks (00 to ff)
chunks = {f"{i:02x}": {} for i in range(256)}
search_index = {}

for name, payload in all_characters.items():
    chunk_id = hashlib.md5(name.lower().encode("utf-8")).hexdigest()[:2]
    chunks[chunk_id][name] = payload

    # Build autocomplete prefix
    prefix = name[:3].lower()
    if prefix not in search_index:
        search_index[prefix] = []
    search_index[prefix].append([name, chunk_id])

# Write chunk files
for chunk_id, bucket_data in chunks.items():
    chunk_file = os.path.join(CHUNKS_DIR, f"chunk_{chunk_id}.json")
    with open(chunk_file, "w", encoding="utf-8") as f:
        json.dump(bucket_data, f, ensure_ascii=False)

# Write search index
with open(INDEX_PATH, "w", encoding="utf-8") as f:
    json.dump(search_index, f, ensure_ascii=False)

print("Merging complete. Sharded files are ready in data/ for GitHub Pages!")

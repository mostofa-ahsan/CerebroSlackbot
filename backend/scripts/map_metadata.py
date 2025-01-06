import json

SUMMARY_FILE = "../data/scrap_summary_{timestamp}.json"
MAPPED_METADATA_FILE = "../data/mapped_metadata.json"

def map_metadata():
    """Map metadata from the summary JSON."""
    with open(SUMMARY_FILE, "r") as f:
        data = json.load(f)

    metadata_mapping = []
    for entry in data:
        metadata_mapping.append({
            "page_id": entry["visited_page_id"],
            "page_link": entry["visited_page_link"],
            "downloads": entry["downloadable_file_list"],
            "images": entry["image_list"],
            "child_links": entry["child_web_links"]
        })

    with open(MAPPED_METADATA_FILE, "w") as f:
        json.dump(metadata_mapping, f, indent=4)
    print(f"Mapped metadata saved to {MAPPED_METADATA_FILE}")

if __name__ == "__main__":
    map_metadata()

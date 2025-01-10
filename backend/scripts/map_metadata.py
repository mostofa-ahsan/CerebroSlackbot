import json
import os

def map_metadata(progress_file, mapped_metadata_file, index_dir, embedding_dir):
    """
    Map metadata from the progress summary JSON for Neo4j.
    Includes child_pages, download_list, parent_pages, embeddings, and indexes.
    """
    # Ensure progress file exists
    if not os.path.exists(progress_file):
        print(f"Error: {progress_file} not found.")
        return

    # Load progress data
    with open(progress_file, "r") as f:
        progress_data = json.load(f)

    metadata = {
        "nodes": [],
        "relationships": []
    }

    for entry in progress_data:
        # Add Page Node
        metadata["nodes"].append({
            "id": entry["page_id"],
            "label": "Page",
            "properties": {
                "page_link": entry["page_link"],
                "saved_as_pdf": entry["saved_as_pdf"],
                "saved_as_html": entry["saved_as_html"]
            }
        })

        # Add Parent Page Relationships
        for parent_page in entry.get("parent_pages", []):
            if parent_page:
                metadata["relationships"].append({
                    "start": parent_page,
                    "end": entry["page_id"],
                    "type": "CHILD_OF"
                })

        # Add Child Page Relationships
        for child_page in entry.get("child_pages", []):
            if child_page:
                metadata["relationships"].append({
                    "start": entry["page_id"],
                    "end": child_page,
                    "type": "LINKS_TO"
                })

        # Add Download Nodes and Relationships
        for download in entry.get("download_list", []):
            if download:
                file_id = f"file_{os.path.basename(download)}"
                metadata["nodes"].append({
                    "id": file_id,
                    "label": "File",
                    "properties": {
                        "path": download
                    }
                })
                metadata["relationships"].append({
                    "start": entry["page_id"],
                    "end": file_id,
                    "type": "CONTAINS"
                })

        # Add Image Nodes and Relationships
        for image in entry.get("saved_images_list", []):
            if image:  # Skip if the image entry is None
                image_id = f"image_{os.path.basename(image)}"
                metadata["nodes"].append({
                    "id": image_id,
                    "label": "Image",
                    "properties": {
                        "path": image
                    }
                })
                metadata["relationships"].append({
                    "start": entry["page_id"],
                    "end": image_id,
                    "type": "CONTAINS"
                })

        # Add Index Nodes and Relationships
        index_file = os.path.join(index_dir, f"{entry['page_id']}_index.json")
        if os.path.exists(index_file):
            metadata["nodes"].append({
                "id": f"index_{entry['page_id']}",
                "label": "Index",
                "properties": {
                    "path": index_file
                }
            })
            metadata["relationships"].append({
                "start": entry["page_id"],
                "end": f"index_{entry['page_id']}",
                "type": "INDEXED_BY"
            })

        # Add Embedding Nodes and Relationships
        embedding_file = os.path.join(embedding_dir, f"{entry['page_id']}_embedding.json")
        if os.path.exists(embedding_file):
            metadata["nodes"].append({
                "id": f"embedding_{entry['page_id']}",
                "label": "Embedding",
                "properties": {
                    "path": embedding_file
                }
            })
            metadata["relationships"].append({
                "start": entry["page_id"],
                "end": f"embedding_{entry['page_id']}",
                "type": "REPRESENTED_BY"
            })

    # Save mapped metadata
    with open(mapped_metadata_file, "w") as f:
        json.dump(metadata, f, indent=4)
    print(f"Mapped metadata saved to {mapped_metadata_file}")


if __name__ == "__main__":
    # Example usage for testing
    DATA_DIR = "../data"
    progress_file = os.path.join(DATA_DIR, "progress_summary.json")
    mapped_metadata_file = os.path.join(DATA_DIR, "mapped_metadata.json")
    index_dir = os.path.join(DATA_DIR, "indexes")
    embedding_dir = os.path.join(DATA_DIR, "embeddings")

    map_metadata(progress_file, mapped_metadata_file, index_dir, embedding_dir)

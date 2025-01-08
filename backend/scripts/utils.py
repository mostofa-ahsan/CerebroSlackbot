import os
import json
import glob

def get_most_recent_file(pattern):
    """Get the most recent file matching a pattern."""
    files = glob.glob(pattern)
    return max(files, key=os.path.getctime) if files else None

def load_links_from_file(file_path):
    """Load links from a file into a set."""
    try:
        with open(file_path, "r") as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        return set()

def save_links_to_file(links, file_path):
    """Save a set of links to a file."""
    with open(file_path, "w") as f:
        for link in sorted(links):
            f.write(f"{link}\n")

def combine_scrap_summaries(files, output_file):
    """Combine multiple scrap_summary JSON files into one."""
    combined = []
    for file in files:
        try:
            with open(file, "r") as f:
                combined.extend(json.load(f))
        except Exception as e:
            print(f"Error reading {file}: {e}")

    with open(output_file, "w") as f:
        json.dump(combined, f, indent=4)

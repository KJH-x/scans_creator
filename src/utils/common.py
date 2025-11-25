import hashlib
from pathlib import Path


def calculate_sha256(json_file_path: str | Path):
    """
    Read the JSON file, remove whitespace,
    then calculate the SHA256 hash of the cleaned JSON string.

    Args:
        json_file_path (str): Path to the JSON file to be processed.

    Returns:
        str: SHA256 hash of the processed JSON string.
    """
    with open(json_file_path, "r", encoding="utf-8") as file:
        file_content = file.read()

    # remove all whitespace characters (spaces, newlines, etc.)
    cleaned_content = "".join(file_content.split())
    sha256_hash = hashlib.sha256(cleaned_content.encode("utf-8")).hexdigest()
    return sha256_hash


if __name__ == "__main__":
    # for development
    json_path = Path(__file__).parent.parent / "config/schemas/defaults.json.bak"
    print(f'self.defaults_SHA256 = "{calculate_sha256(json_path)}"')

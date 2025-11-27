import hashlib
import json
from pathlib import Path


def calculate_json_sha256(json_file_path: Path) -> str:
    """
    Read the JSON file, normalize it by removing formatting whitespace
    but keeping internal string spaces, then compute SHA256.
    """
    try:
        with open(json_file_path, "r", encoding="utf-8") as file:
            obj = json.load(file)

        normalized = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    except Exception as e:
        raise RuntimeError(f"Failed to calculate JSON SHA256: {e}") from e


if __name__ == "__main__":
    # for development
    json_path = Path(__file__).parents[2] / "config/schemas/defaults.json.bak"
    print(f'self.defaults_SHA256 = "{calculate_json_sha256(json_path)}"')

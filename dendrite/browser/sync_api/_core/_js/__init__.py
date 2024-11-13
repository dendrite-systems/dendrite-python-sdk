from pathlib import Path


def load_script(filename: str) -> str:
    current_dir = Path(__file__).parent
    file_path = current_dir / filename
    return file_path.read_text(encoding="utf-8")


GENERATE_DENDRITE_IDS_SCRIPT = load_script("generateDendriteIDs.js")
GENERATE_DENDRITE_IDS_IFRAME_SCRIPT = load_script("generateDendriteIDsIframe.js")

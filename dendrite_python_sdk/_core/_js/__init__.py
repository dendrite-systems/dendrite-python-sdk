import os

_base_dir = os.path.dirname(__file__)


def load_script(filename: str) -> str:

    path = os.path.join(_base_dir, filename)

    with open(path, encoding="utf-8") as f:
        return f.read()


GENERATE_DENDRITE_IDS_SCRIPT = load_script("generateDendriteIDs.js")
GENERATE_DENDRITE_IDS_IFRAME_SCRIPT = load_script("generateDendriteIDsIframe.js")

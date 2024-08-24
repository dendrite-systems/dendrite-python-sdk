import os

_base_dir = os.path.dirname(__file__)


def load_script(filename: str) -> str:

    path = os.path.join(_base_dir, filename)

    with open(path, encoding="utf-8") as f:
        return f.read()


GENERATE_DENDRITE_IDS_SCRIPT = load_script("generateDendriteIDs.js")
TEST_GEN_IDS_SCRIPT = load_script("testGenIds.js")
CLOSED_SHADOW_DOM_PATCH_SCRIPT = load_script("closedSHadowDomPatch.js")
TEST_SCRIPT = load_script("test.js")

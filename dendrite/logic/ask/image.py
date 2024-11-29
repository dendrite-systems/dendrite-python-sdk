import base64
import io
from typing import List

from loguru import logger
from PIL import Image


def segment_image(
    base64_image: str,
    segment_height: int = 7900,
) -> List[str]:
    if len(base64_image) < 100:
        raise Exception("Failed to segment image since it is too small / glitched.")

    image_data = base64.b64decode(base64_image)
    image = Image.open(io.BytesIO(image_data))
    width, height = image.size
    segments = []

    for i in range(0, height, segment_height):
        # Define the box for cropping (left, upper, right, lower)
        box = (0, i, width, min(i + segment_height, height))
        segment = image.crop(box)

        # Convert RGBA to RGB if necessary
        if segment.mode == "RGBA":
            segment = segment.convert("RGB")

        buffer = io.BytesIO()
        segment.save(buffer, format="JPEG")
        segment_data = buffer.getvalue()
        segments.append(base64.b64encode(segment_data).decode())

    return segments

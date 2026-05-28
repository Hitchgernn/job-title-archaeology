import os
import re
from pathlib import Path

from google import genai
from google.genai import types

from backend.archive.models import ArchiveEditorialMetadata
from backend.trends.models import TrendResult


class ImageProviderError(RuntimeError):
    pass


class GeminiImageProvider:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        resolved_key = api_key or os.getenv("GEMINI_API_KEY")
        if not resolved_key:
            raise ImageProviderError("GEMINI_API_KEY is required")

        self.model = model or os.getenv(
            "GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image-preview"
        )
        self.client = genai.Client(api_key=resolved_key)

    def generate(self, prompt: str) -> bytes:
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
        )
        for candidate in response.candidates or []:
            content = getattr(candidate, "content", None)
            for part in getattr(content, "parts", None) or []:
                if getattr(part, "inline_data", None) is not None:
                    return part.inline_data.data
        raise ImageProviderError("Gemini response did not include image bytes")


def image_filename(trend: TrendResult) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", trend.display_title.casefold()).strip("-")
    if not slug:
        slug = "title"
    return f"{trend.normalized_title_id}-{slug}.png"


def build_archive_image_prompt(
    trend: TrendResult, metadata: ArchiveEditorialMetadata
) -> str:
    return (
        "Create a monochrome black-and-white archival newspaper illustration for "
        f"the job title {trend.display_title}. "
        f"Category: {metadata.category}. "
        f"Sector: {metadata.sector}. "
        f"Editorial pull quote mood: {metadata.pull_quote}. "
        "Use period-appropriate print texture, engraved halftone shading, "
        "documentary composition, and human-scale workplace symbolism. "
        "Do not include readable text, logos, brand names, UI, watermarks, or color."
    )


def save_image_bytes(output_dir: Path, filename: str, content: bytes) -> str:
    path = Path(filename)
    if path.name != filename or path.suffix.casefold() != ".png":
        raise ValueError("invalid image filename")

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / filename).write_bytes(content)
    return f"/archive-generated/{filename}"

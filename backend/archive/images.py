import re
from pathlib import Path

from backend.archive.models import ArchiveEditorialMetadata
from backend.trends.models import TrendResult


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

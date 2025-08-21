from pathlib import Path

__all__ = ["srt_to_txt", "srt_to_vtt"]


def srt_to_txt(srt_path: Path) -> str:
    """Convert an SRT file to plain text."""
    lines = []
    for line in srt_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.isdigit():
            continue
        if "-->" in stripped:
            continue
        lines.append(stripped)
    return "\n".join(lines)


def srt_to_vtt(srt_path: Path) -> str:
    """Convert an SRT file to WebVTT format."""
    output = ["WEBVTT", ""]
    for line in srt_path.read_text(encoding="utf-8").splitlines():
        if "-->" in line:
            line = line.replace(",", ".")
        output.append(line)
    return "\n".join(output)

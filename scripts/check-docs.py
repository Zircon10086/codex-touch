#!/usr/bin/env python3
"""Check bilingual Markdown navigation, local links, and release versions."""
from pathlib import Path
import re
import unicodedata
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def prose(text):
    return re.sub(r"(?ms)^```[^\n]*\n.*?^```[^\n]*$", "", text)


def anchors(text):
    seen = {}
    result = set()
    for heading in re.findall(r"(?m)^#{1,6}\s+(.+?)\s*#*\s*$", prose(text)):
        heading = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", heading)
        heading = heading.replace("`", "").lower()
        slug = "".join(c for c in heading if c in "_- " or unicodedata.category(c)[0] in "LN").replace(" ", "-")
        count = seen.get(slug, 0)
        seen[slug] = count + 1
        result.add(f"{slug}-{count}" if count else slug)
    return result


def main():
    documents = sorted([*ROOT.glob("*.md"), *(p for folder in ("docs", "src", "tests") for p in (ROOT / folder).rglob("*.md"))])
    errors = []
    for path in documents:
        text = path.read_text()
        chinese = path.name.endswith(".zh-CN.md")
        peer = path.with_name(path.name.replace(".zh-CN.md", ".md")) if chinese else path.with_suffix(".zh-CN.md")
        if not peer.is_file():
            errors.append(f"{path.relative_to(ROOT)}: missing translation {peer.name}")
        if f"]({peer.name})" not in text.splitlines()[0]:
            errors.append(f"{path.relative_to(ROOT)}: missing top language link")
        if not chinese and re.search(r"[\u3400-\u9fff]", prose(text).split("\n", 1)[-1]):
            errors.append(f"{path.relative_to(ROOT)}: non-English default prose")
        body = prose(text)
        links = re.findall(r"\]\(([^\s)]+)\)", body)
        links += re.findall(r"(?m)^\[[^]]+\]:\s*(\S+)", body)
        for link in links:
            target = urlsplit(link)
            if target.scheme or target.netloc:
                continue
            destination = (path.parent / unquote(target.path)).resolve() if target.path else path
            if not destination.is_relative_to(ROOT) or not destination.exists():
                errors.append(f"{path.relative_to(ROOT)}: missing/escaping link {link}")
            elif target.fragment and destination.suffix == ".md" and unquote(target.fragment) not in anchors(destination.read_text()):
                errors.append(f"{path.relative_to(ROOT)}: missing heading {link}")
    version = (ROOT / "VERSION").read_text().strip()
    for suffix in (".md", ".zh-CN.md"):
        if f"**{version}**" not in (ROOT / ("README" + suffix)).read_text():
            errors.append(f"README{suffix}: version mismatch")
        if f"## [{version}] - " not in (ROOT / ("CHANGELOG" + suffix)).read_text():
            errors.append(f"CHANGELOG{suffix}: version entry missing")
    if errors:
        raise SystemExit("\n".join("FAIL: " + error for error in errors))
    print(f"PASS: {len(documents) // 2} English/Chinese document pairs, language links, local links, and version {version}.")


if __name__ == "__main__":
    main()

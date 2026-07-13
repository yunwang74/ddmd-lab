#!/usr/bin/env python3
"""Refresh publications.html from the public ORCID works feed."""

from __future__ import annotations

import html
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from urllib.request import Request, urlopen

ORCID_ID = os.getenv("ORCID_ID", "0000-0001-8619-0455")
API = f"https://pub.orcid.org/v3.0/{ORCID_ID}/works"
HEADERS = {"Accept": "application/vnd.orcid+xml"}


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def direct_children(node, name: str):
    return [child for child in list(node) if local_name(child.tag) == name]


def first_child(node, name: str):
    for child in list(node):
        if local_name(child.tag) == name:
            return child
    return None


def child_text(node, name: str, default: str = "") -> str:
    child = first_child(node, name)
    if child is None:
        return default
    value = "".join(child.itertext()).strip()
    return value or default


def parse_int(value: str | None, default: int = 0) -> int:
    try:
        return int(value or default)
    except (TypeError, ValueError):
        return default


def fetch_orcid_xml() -> ET.Element:
    print(f"Fetching ORCID works for {ORCID_ID}...", file=sys.stderr)
    try:
        request = Request(API, headers=HEADERS)
        with urlopen(request, timeout=30) as response:
            payload = response.read().decode("utf-8")
    except Exception as exc:
        raise RuntimeError(f"ORCID fetch failed: {exc}") from exc

    try:
        return ET.fromstring(payload)
    except ET.ParseError as exc:
        raise RuntimeError(f"ORCID parse failed: {exc}") from exc


def extract_best_work_summary(group):
    summaries = direct_children(group, "work-summary")
    if not summaries:
        return None
    return max(summaries, key=lambda summary: parse_int(summary.attrib.get("display-index")))


def extract_work(summary):
    title_wrapper = first_child(summary, "title")
    title = child_text(title_wrapper, "title") if title_wrapper is not None else child_text(summary, "title")
    title = " ".join(title.split())
    if not title:
        return None

    journal = " ".join(child_text(summary, "journal-title").split())
    publication_date = first_child(summary, "publication-date")
    year = child_text(publication_date, "year") if publication_date is not None else ""
    year = year.strip()

    external_ids = first_child(summary, "external-ids")
    doi = ""
    if external_ids is not None:
        for external_id in direct_children(external_ids, "external-id"):
            if child_text(external_id, "external-id-type").lower() == "doi":
                doi = child_text(external_id, "external-id-value").strip()
                break
    doi = (
        doi.removeprefix("https://doi.org/")
        .removeprefix("http://doi.org/")
        .removeprefix("doi:")
    )

    url = child_text(summary, "url").strip()
    if not url and doi:
        url = f"https://doi.org/{doi}"

    return {
        "title": title,
        "journal": journal,
        "year": year,
        "url": url,
        "doi": doi,
    }


def collect_items(root: ET.Element):
    groups = direct_children(root, "group")
    items = []
    for group in groups:
        summary = extract_best_work_summary(group)
        if summary is None:
            continue
        item = extract_work(summary)
        if item is not None:
            items.append(item)

    deduped = []
    seen = set()
    for item in items:
        key = item["doi"].lower() if item["doi"] else (
            item["title"].lower(),
            item["journal"].lower(),
            item["year"],
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    deduped.sort(
        key=lambda item: (
            parse_int(item["year"], 0),
            item["title"].lower(),
        ),
        reverse=True,
    )
    return deduped


def render_item(item):
    title = html.escape(item["title"])
    journal = html.escape(item["journal"])
    year = html.escape(item["year"] or "n.d.")
    doi = html.escape(item["doi"])
    link = html.escape(item["url"], quote=True) if item["url"] else ""
    link_html = (
        f" <a class='doi-link' href='{link}' target='_blank' rel='noopener'>DOI</a>"
        if link
        else ""
    )
    badge_html = f" <span class='badge badge-doi'>{doi}</span>" if doi else ""
    journal_html = f" - <em>{journal}</em>" if journal else ""
    return f"<li><strong>{title}</strong>{journal_html} ({year}).{link_html}{badge_html}</li>"


def render_selected(items):
    if not items:
        return '<li class="muted">No recent items found.</li>'
    return "\n".join(render_item(item) for item in items[:12])


def render_grouped(items):
    by_year = defaultdict(list)
    for item in items:
        by_year[item["year"] or "n.d."].append(item)

    if not by_year:
        return '<p class="muted">No grouped items found.</p>'

    def year_sort_key(year):
        return (parse_int(year, -1), year)

    blocks = []
    for year in sorted(by_year.keys(), key=year_sort_key, reverse=True):
        rows = "\n".join(render_item(item) for item in by_year[year])
        blocks.append(f"<h3>{html.escape(year)}</h3>\n<ul>\n{rows}\n</ul>")
    return '<div class="pubs-by-year">\n' + "\n".join(blocks) + "\n</div>"


def replace_section(text: str, start_marker: str, end_marker: str, replacement: str) -> str:
    pattern = re.compile(
        re.escape(start_marker) + r".*?" + re.escape(end_marker),
        re.DOTALL,
    )
    new_text, count = pattern.subn(start_marker + replacement + end_marker, text, count=1)
    if count == 0:
        raise RuntimeError(f"Could not find section between {start_marker} and {end_marker}")
    return new_text


def main() -> int:
    root = fetch_orcid_xml()
    items = collect_items(root)
    selected_html = "<ul>\n" + render_selected(items) + "\n</ul>"
    grouped_html = render_grouped(items)

    with open("publications.html", "r", encoding="utf-8") as handle:
        original = handle.read()

    updated = replace_section(
        original,
        "<!-- AUTO-PUBS-START -->",
        "<!-- AUTO-PUBS-END -->",
        "\n" + selected_html + "\n",
    )
    updated = replace_section(
        updated,
        "<!-- AUTO-PUBS-YEAR-START -->",
        "<!-- AUTO-PUBS-YEAR-END -->",
        "\n" + grouped_html + "\n",
    )

    if updated != original:
        with open("publications.html", "w", encoding="utf-8", newline="\n") as handle:
            handle.write(updated)
        print("Updated publications.html", file=sys.stderr)
    else:
        print("No changes to publications.html", file=sys.stderr)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1)


#!/usr/bin/env python3
import os, sys, json, html
from urllib.request import Request, urlopen
from collections import defaultdict

ORCID_ID = "0000-0001-8619-0455"
API = f"https://pub.orcid.org/v3.0/{ORCID_ID}/works"
HEADERS = {"Accept": "application/json"}

print("Fetching ORCID works…", file=sys.stderr)
try:
    data = json.loads(urlopen(Request(API, headers=HEADERS)).read().decode("utf-8"))
except Exception as e:
    print("ORCID fetch failed:", e, file=sys.stderr)
    data = {}

items = []
try:
    for g in data.get("group", []):
        for w in g.get("work-summary", []):
            title = w.get("title", {}).get("title", {}).get("value", "Untitled")
            journal = w.get("journal-title", {}).get("value", "")
            year = (w.get("publication-date", {}) or {}).get("year", {}).get("value", "")
            doi = None
            for ext in w.get("external-ids", {}).get("external-id", []):
                if (ext.get("external-id-type") or "").lower() == "doi":
                    doi = ext.get("external-id-value"); break
            url = f"https://doi.org/{doi}" if doi else None
            items.append({"title": title, "journal": journal, "year": year, "url": url, "doi": doi})
except Exception as e:
    print("Parse error:", e, file=sys.stderr)

items = [i for i in items if i.get("year")]
try:
    items.sort(key=lambda x: str(x["year"]), reverse=True)
except Exception:
    items.sort(key=lambda x: (x.get("year") or ""), reverse=True)

# Selected publications (top 12) — show DOI string on badge
sel_html = []
for it in items[:12]:
    t = html.escape(it['title'])
    j = html.escape(it['journal']) if it['journal'] else ''
    y = html.escape(str(it['year']))
    u = it['url']
    doi_str = html.escape(it.get('doi') or '')
    dash = " — " if j else ""
    doi_link = f" <a class='doi-link' href='{u}' target='_blank' rel='noopener'>DOI</a>" if u else ""
    doi_badge = f" <span class='badge badge-doi'>{doi_str}</span>" if doi_str else ""
    sel_html.append(f"<li><strong>{t}</strong>{dash}<em>{j}</em> ({y}).{doi_link}{doi_badge}</li>")
new_list_html = " ".join(sel_html) if sel_html else '<li class="muted">No recent items found.</li>'

# Group by year — show DOI string on badge
by_year = defaultdict(list)
for it in items:
    by_year[it['year']].append(it)

years_sorted = sorted(by_year.keys(), reverse=True)
blocks = []
for y in years_sorted:
    lis = []
    for it in by_year[y]:
        t = html.escape(it['title'])
        j = html.escape(it['journal']) if it['journal'] else ''
        u = it['url']
        doi_str = html.escape(it.get('doi') or '')
        dash = " — " if j else ""
        doi_link = f" <a class='doi-link' href='{u}' target='_blank' rel='noopener'>DOI</a>" if u else ""
        doi_badge = f" <span class='badge badge-doi'>{doi_str}</span>" if doi_str else ""
        lis.append(f"<li><strong>{t}</strong>{dash}<em>{j}</em>{doi_link}{doi_badge}</li>")
    block_html = f"<h3>{html.escape(str(y))}</h3> <ul> " + "  ".join(lis) + " </ul>"
    blocks.append(block_html)
new_group_html = " ".join(blocks) if blocks else '<p class="muted">No grouped items.</p>'

# Update publications.html
with open("publications.html", 'r', encoding='utf-8') as f:
    html_text = f.read()

start = html_text.find("<!-- AUTO-PUBS-START -->")
end = html_text.find("<!-- AUTO-PUBS-END -->")
if start != -1 and end != -1:
    before = html_text[:start]
    after = html_text[end:]
    middle = (
        "<!-- AUTO-PUBS-START -->" +
        "<ul>" + new_list_html + "</ul>" +
        "<!-- AUTO-PUBS-END -->"
    )
    html_text = before + middle + after

start2 = html_text.find("<!-- AUTO-PUBS-YEAR-START -->")
end2 = html_text.find("<!-- AUTO-PUBS-YEAR-END -->")
if start2 != -1 and end2 != -1:
    before2 = html_text[:start2]
    after2 = html_text[end2:]
    middle2 = (
        "<!-- AUTO-PUBS-YEAR-START -->" +
        '<div class="pubs-by-year">' + new_group_html + "</div>" +
        "<!-- AUTO-PUBS-YEAR-END -->"
    )
    html_text = before2 + middle2 + after2

with open("publications.html", 'r', encoding='utf-8') as f:
    original = f.read()
if html_text != original:
    with open("publications.html", 'w', encoding='utf-8') as f:
        f.write(html_text)
    print("Updated publications.html", file=sys.stderr)
else:
    print("No changes to publications.html", file=sys.stderr)

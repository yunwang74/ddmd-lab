
#!/usr/bin/env python3
import os, sys, json, subprocess, html
from urllib.request import Request, urlopen
from collections import defaultdict

ORCID_ID = "0000-0001-8619-0455"
TOKEN = os.environ.get("ORCID_TOKEN")
API = f"https://pub.orcid.org/v3.0/{ORCID_ID}/works"
HEADERS = {"Accept":"application/json"}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"

print("Fetching ORCID works…", file=sys.stderr)
req = Request(API, headers=HEADERS)
try:
    data = json.loads(urlopen(req).read().decode("utf-8"))
except Exception as e:
    print("ORCID fetch failed:", e, file=sys.stderr)
    sys.exit(0)  # fail gracefully

items = []
try:
    group = data.get("group", [])
    for g in group:
        for w in g.get("work-summary", []):
            title = w.get("title", {}).get("title", {}).get("value", "Untitled")
            journal = w.get("journal-title", {}).get("value", "")
            year = (w.get("publication-date", {}) or {}).get("year", {}).get("value", "")
            url = None
            for ext in w.get("external-ids", {}).get("external-id", []):
                if ext.get("external-id-type") == "doi":
                    doi = ext.get("external-id-value");
                    url = f"https://doi.org/{doi}" if doi else None
                    break
            items.append({"title":title, "journal":journal, "year":year, "url":url})
except Exception as e:
    print("Parse error:", e, file=sys.stderr)

# Filter items with a year and sort desc
items = [i for i in items if i.get("year")]
items.sort(key=lambda x: x["year"], reverse=True)

# Build selected recent list (top 12)
sel_html = []
for it in items[:12]:
    t = html.escape(it['title']); j = html.escape(it['journal']) if it['journal'] else ''; y = html.escape(str(it['year'])); u = it['url']
    sel_html.append(f"<li><strong>{t}</strong> — <em>{j}</em> ({y})." + (f" <a href='{u}' target='_blank' rel='noopener'>DOI</a>" if u else "") + "</li>")
new_list_html = "
".join(sel_html) if sel_html else "<!-- No items parsed from ORCID -->"

# Group by year
by_year = defaultdict(list)
for it in items:
    by_year[it['year']].append(it)

# Build grouped HTML
years_sorted = sorted(by_year.keys(), reverse=True)
blocks = []
for y in years_sorted:
    lis = []
    for it in by_year[y]:
        t = html.escape(it['title']); j = html.escape(it['journal']) if it['journal'] else ''; u = it['url']
        lis.append(f"<li><strong>{t}</strong> — <em>{j}</em>" + (f" <a href='{u}' target='_blank' rel='noopener'>DOI</a>" if u else "") + "</li>")
    ul = "
".join(lis)
    blocks.append(f"<h3>{y}</h3>
<ul>
{ul}
</ul>")
new_group_html = "
".join(blocks) if blocks else "<!-- No grouped items -->"

# Replace markers in publications.html
pub_path = "publications.html"
with open(pub_path, 'r', encoding='utf-8') as f:
    html_text = f.read()

# Selected list markers
start = html_text.find("<!-- AUTO-PUBS-START -->")
end = html_text.find("<!-- AUTO-PUBS-END -->")
if start != -1 and end != -1:
    before = html_text[:start]
    after = html_text[end:]
    middle = f"<!-- AUTO-PUBS-START -->
<ul>
{new_list_html}
</ul>
<!-- AUTO-PUBS-END -->"
    html_text = before + middle + after

# Grouped section markers
start2 = html_text.find("<!-- AUTO-PUBS-YEAR-START -->")
end2 = html_text.find("<!-- AUTO-PUBS-YEAR-END -->")
if start2 != -1 and end2 != -1:
    before2 = html_text[:start2]
    after2 = html_text[end2:]
    middle2 = f"<!-- AUTO-PUBS-YEAR-START -->
<div class="pubs-by-year">
{new_group_html}
</div>
<!-- AUTO-PUBS-YEAR-END -->"
    html_text = before2 + middle2 + after2

with open(pub_path, 'w', encoding='utf-8') as f:
    f.write(html_text)

print("Publications updated (selected + by year)", file=sys.stderr)

# Commit if changes
subprocess.run(["git", "config", "user.name", "github-actions"], check=False)
subprocess.run(["git", "config", "user.email", "actions@github.com"], check=False)
subprocess.run(["git", "add", "publications.html"], check=False)
subprocess.run(["git", "commit", "-m", "Auto-update publications (selected + by year)"], check=False)

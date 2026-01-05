#!/usr/bin/env python3
import os, sys, json, subprocess, html
from urllib.request import Request, urlopen
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
    print("ORCID fetch failed:", e, file=sys.stderr); sys.exit(0)
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
                    doi = ext.get("external-id-value"); url = f"https://doi.org/{doi}" if doi else None; break
            items.append({"title":title, "journal":journal, "year":year, "url":url})
except Exception as e:
    print("Parse error:", e, file=sys.stderr)
items = [i for i in items if i.get("year")]; items.sort(key=lambda x: x["year"], reverse=True); items = items[:12]
lis = []
for it in items:
    t = html.escape(it['title']); j = html.escape(it['journal']) if it['journal'] else ''; y = html.escape(str(it['year'])) if it['year'] else ''; u = it['url']
    lis.append(f"<li><strong>{t}</strong> — <em>{j}</em> ({y})." + (f" <a href='{u}' target='_blank' rel='noopener'>DOI</a>" if u else "") + "</li>")
new_list_html = "
".join(lis) if lis else "<!-- No items parsed from ORCID -->"
pub_path = "publications.html"
with open(pub_path, 'r', encoding='utf-8') as f:
    html_text = f.read()
start = html_text.find("<!-- AUTO-PUBS-START -->"); end = html_text.find("<!-- AUTO-PUBS-END -->")
if start != -1 and end != -1:
    before = html_text[:start]; after = html_text[end:]
    middle = f"<!-- AUTO-PUBS-START -->
<ul>
{new_list_html}
</ul>
<!-- AUTO-PUBS-END -->"
    with open(pub_path, 'w', encoding='utf-8') as f:
        f.write(before + middle + after)
    print("Updated publications.html", file=sys.stderr)
subprocess.run(["git", "config", "user.name", "github-actions"], check=False)
subprocess.run(["git", "config", "user.email", "actions@github.com"], check=False)
subprocess.run(["git", "add", "publications.html"], check=False)
subprocess.run(["git", "commit", "-m", "Update publications from ORCID"], check=False)

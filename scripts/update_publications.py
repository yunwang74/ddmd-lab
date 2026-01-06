
#!/usr/bin/env python3
import os, sys, json, html
from urllib.request import Request, urlopen
from collections import defaultdict

ORCID_ID = "0000-0001-8619-0455"
TOKEN = os.environ.get("ORCID_TOKEN")
API = f"https://pub.orcid.org/v3.0/{ORCID_ID}/works"
HEADERS = {"Accept": "application/json"}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"

print("Fetching ORCID works…", file=sys.stderr)
try:
    resp = urlopen(Request(API, headers=HEADERS))
    data = json.loads(resp.read().decode("utf-8"))
except Exception as e:
    print("ORCID fetch failed:", e, file=sys.stderr)
    # Continue gracefully: we'll write "No items" to the page
    data = {}

# ---- Build items (must happen BEFORE we iterate over items) ----
items = []
try:
    for g in data.get("group", []):
        for w in g.get("work-summary", []):
            title = w.get("title", {}).get("title", {}).get("value", "Untitled")
            journal = w.get("journal-title", {}).get("value", "")
            year = (w.get("publication-date", {}) or {}).get("year", {}).get("value", "")
            doi = None
            for ext in w.get("external-ids", {}).get("external-id", []):
                # Be robust to case variations
                if (ext.get("external-id-type") or "").lower() == "doi":
                    doi = ext.get("external-id-value")
                    break
            url = f"https://doi.org/{doi}" if doi else None
            items.append({"title": title, "journal": journal, "year": year, "url": url})
except Exception as e:
    print("Parse error:", e, file=sys.stderr)

# Filter and sort
items = [i for i in items if i.get("year")]
try:
    items.sort(key=lambda x: str(x["year"]), reverse=True)
except Exception:
    # Fallback if some years are weird
    items.sort(key=lambda x: (x.get("year") or ""), reverse=True)

# ---- Recent list (top 12) ----
sel_html = []
for it in items[:12]:
    t = html.escape(it['title'])
    j = html.escape(it['journal']) if it['journal'] else ''
    y = html.escape(str(it['year']))
    u = it['url']
    dash = " — " if j else ""
    sel_html.append(
        f"&lt;li&gt;&lt;strong&gt;{t}&lt;/strong&gt;{dash}&lt;em&gt;{j}&lt;/em&gt; ({y})."
        + (f" &lt;a href='{u}' target='_blank' rel='noopener'&gt;DOI&lt;/a&gt;" if u else "")
        + "&lt;/li&gt;"
    )

# Use single quotes so class="muted" doesn't break the outer quotes
new_list_html = " ".join(sel_html) if sel_html else '&lt;li class="muted"&gt;No recent items found.&lt;/li&gt;'

# ---- Group by year ----
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
        dash = " — " if j else ""
        lis.append(
            f"&lt;li&gt;&lt;strong&gt;{t}&lt;/strong&gt;{dash}&lt;em&gt;{j}&lt;/em&gt;"
            + (f" &lt;a href='{u}' target='_blank' rel='noopener'&gt;DOI&lt;/a&gt;" if u else "")
            + "&lt;/li&gt;"
        )

    block_html = (
        f"&lt;h3&gt;{html.escape(str(y))}&lt;/h3&gt;\n"
        "&lt;ul&gt;\n"
        + "\n".join(lis) + "\n"
        "&lt;/ul&gt;"
    )
    blocks.append(block_html)

new_group_html = "\n".join(blocks) if blocks else '&lt;p class="muted"&gt;No grouped items.&lt;/p&gt;'

# ---- Update publications.html ----
with open("publications.html", 'r', encoding='utf-8') as f:
    html_text = f.read()

# Recent list section
start = html_text.find("&lt;!-- AUTO-PUBS-START --&gt;")
end = html_text.find("&lt;!-- AUTO-PUBS-END --&gt;")
if start != -1 and end != -1:
    before = html_text[:start]
    after = html_text[end:]
    middle = (
        "&lt;!-- AUTO-PUBS-START --&gt;\n"
        "&lt;ul&gt;\n"
        f"{new_list_html}\n"
        "&lt;/ul&gt;\n"
        "&lt;!-- AUTO-PUBS-END --&gt;"
    )
    html_text = before + middle + after

# Grouped-by-year section
start2 = html_text.find("&lt;!-- AUTO-PUBS-YEAR-START --&gt;")
end2 = html_text.find("&lt;!-- AUTO-PUBS-YEAR-END --&gt;")
if start2 != -1 and end2 != -1:
    before2 = html_text[:start2]
    after2 = html_text[end2:]
    middle2 = (
        "&lt;!-- AUTO-PUBS-YEAR-START --&gt;\n"
        '&lt;div class="pubs-by-year"&gt;\n'
        f"{new_group_html}\n"
        "&lt;/div&gt;\n"
        "&lt;!-- AUTO-PUBS-YEAR-END --&gt;"
    )
    html_text = before2 + middle2 + after2

with open("publications.html", 'w', encoding='utf-8') as f:
    f.write(html_text)

print("ORCID_TOKEN present:", bool(os.environ.get("ORCID_TOKEN")), file=sys.stderr)

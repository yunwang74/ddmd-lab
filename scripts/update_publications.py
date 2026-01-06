
# --- existing code above stays the same ---

sel_html = []
for it in items[:12]:
    t = html.escape(it['title'])
    j = html.escape(it['journal']) if it['journal'] else ''
    y = html.escape(str(it['year']))
    u = it['url']
    sel_html.append(
        f"&lt;li&gt;&lt;strong&gt;{t}&lt;/strong&gt; — &lt;em&gt;{j}&lt;/em&gt; ({y})."
        + (f" &lt;a href='{u}' target='_blank' rel='noopener'&gt;DOI&lt;/a&gt;" if u else "")
        + "&lt;/li&gt;"
    )

# Use single quotes so class="muted" doesn't break the string
new_list_html = " ".join(sel_html) if sel_html else '&lt;li class="muted"&gt;No recent items found.&lt;/li&gt;'

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
        lis.append(
            f"&lt;li&gt;&lt;strong&gt;{t}&lt;/strong&gt; — &lt;em&gt;{j}&lt;/em&gt;"
            + (f" &lt;a href='{u}' target='_blank' rel='noopener'&gt;DOI&lt;/a&gt;" if u else "")
            + "&lt;/li&gt;"
        )

    # Build the entire block in one go (h3 + ul + li list)
    block_html = (
        f"&lt;h3&gt;{y}&lt;/h3&gt;\n"
        "&lt;ul&gt;\n"
        + "\n".join(lis) + "\n"
        "&lt;/ul&gt;"
    )
    blocks.append(block_html)

# Join blocks safely; use single quotes for the fallback with class="muted"
new_group_html = "\n".join(blocks) if blocks else '&lt;p class="muted"&gt;No grouped items.&lt;/p&gt;'

# --- Update file ---
with open("publications.html", 'r', encoding='utf-8') as f:
    html_text = f.read()

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

print("Updated publications.html", file=sys.stderr)

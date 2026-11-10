#!/usr/bin/env python3
"""Install a single Flashcards nav button with a PDF link in the FAA Part 107 portal.

No git commit or push; no changes to question sets or existing printables.
"""
from pathlib import Path
from hashlib import sha256
import json
import re

root = Path.cwd()
assert root.name == "faa-part-107-exam-simulator", "Run in the FAA Part 107 project directory"
pdf = root / "packs/faa-part-107/pdf/Part107_Flashcards.pdf"
assert pdf.is_file() and pdf.stat().st_size > 10000, "Flashcards PDF missing"
assert pdf.read_bytes().startswith(b"%PDF-"), "Invalid PDF header"
assert sha256(pdf.read_bytes()).hexdigest() == "ba7eca8dee5ae79c4bc138491e66652a1f17b46509c0765ca0e494ecb062a196", "Unexpected flashcards PDF bytes"

config = json.loads((root / "packs/faa-part-107/config.json").read_text(encoding="utf-8"))
assert config.get("examId") == "faa-part-107", "Wrong exam config"
assert len(config.get("examFiles", [])) == 20, "Expected 20 existing full-length exams"
assert config.get("practiceChunkSize") == 30, "Expected Practice Mode to be 30 questions"
assert len(config.get("printables", [])) == 20, "Expected 20 existing printables"

html_file = root / "app/app.html"
html = html_file.read_text(encoding="utf-8")
link_url = "../packs/faa-part-107/pdf/Part107_Flashcards.pdf"
nav_link = f'<a class="navlink" href="{link_url}" target="_blank" rel="noopener noreferrer">Flashcards</a>'

if nav_link not in html:
    pattern = r'(?m)^([ \t]*)<a class="navlink" href="#" data-page="pdf">Printable Practice Exams</a>[ \t]*$'
    matches = list(re.finditer(pattern, html))
    assert len(matches) == 1, "Cannot find unique Printable Practice Exams navbar link"
    m = matches[0]
    html = html[:m.end()] + "\n" + m.group(1) + nav_link + html[m.end():]
    changed = True
else:
    assert html.count(nav_link) == 1, "Unexpected duplicate Flashcards links"
    changed = False

old_selector = 'document.querySelectorAll(".navlink").forEach(link => {'
new_selector = 'document.querySelectorAll(".navlink[data-page]").forEach(link => {'
if old_selector in html:
    assert html.count(old_selector) == 1, "Unexpected navigation handler count"
    html = html.replace(old_selector, new_selector)
    changed = True
else:
    assert html.count(new_selector) == 1, "Navigation handler not found"

assert html.count(nav_link) == 1
assert html.count(new_selector) == 1
assert 'data-page="sim"' in html and 'data-page="pdf"' in html
assert 'id="logoutLink"' in html
assert 'href="' + link_url + '"' in html
if changed:
    html_file.write_text(html, encoding="utf-8")

# The fifth navbar item should not overflow on mobile displays.
style_file = root / "app/styles.css"
css = style_file.read_text(encoding="utf-8")
marker = "/* FAA FLASHCARDS NAV MOBILE WRAP */"
if marker not in css:
    css += "\n" + marker + "\n" + """@media (max-width: 980px) {
  .topbar { flex-wrap: wrap; justify-content: center; gap: 10px; }
  .nav { flex-wrap: wrap; justify-content: center; gap: 8px; }
}
"""
    style_file.write_text(css, encoding="utf-8")

print("=== FAA PART 107 — FLASHCARDS INSTALL ===")
print("PDF: Part107_Flashcards.pdf | VALID | size:", pdf.stat().st_size, "bytes")
print("Flashcards nav button:", "INSTALLED" if changed else "ALREADY PRESENT")
print("Mobile nav wrapping: ENABLED")
print("Opens directly in a new browser tab: YES")
print("20 Full-Length exams and 20 Printable PDFs: UNCHANGED")
print("Practice Mode: 30 questions | UNCHANGED")
print("Git push: NOT EXECUTED")
print("STATUS: OK")

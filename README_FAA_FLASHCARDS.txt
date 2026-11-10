FAA PART 107 — FLASHCARDS NAV BUTTON

Contents:
- Original PDF (265 pages, labeled 500 practice flashcards), unchanged.
- Python installer for adding a Flashcards nav link in app/app.html.

From the faa-part-107-exam-simulator project directory:
  ditto -x -k "$HOME/Downloads/FAA_PART107_FLASHCARDS_BUTTON.zip" .
  python3 tools/install_faa107_flashcards.py

The new Flashcards link opens Part107_Flashcards.pdf directly in a new tab.
This is a PDF viewer link, not an interactive flip-card application.
No questions, printable exams, passwords, or scoring are changed.
A responsive CSS rule prevents the extra nav link from overflowing on small screens.

FAA PART 107 REMOTE PILOT EXAM SIMULATOR — EXAMS 02–19
======================================================

This package adds Exam 02 through Exam 19 to the existing GitHub Pages simulator.
Exam 01 and Exam 20, the logo, and the originals in imports/ are not overwritten.

Contents:
- packs/faa-part-107/data/: 18 JSON files, each 65 questions
- packs/faa-part-107/pdf/: 18 text-only printable PDFs
- tools/install_faa107_remaining.py: offline integrity checks and config installer
- imports/faa_review/FAA107_162_TEXT_ONLY_REWRITE_REVIEW.csv: 162 item-by-item rewrite audit
- imports/faa_review/FAA107_18_EXAM_AUDIT.json: structural summary

The 162 figure-dependent questions (9 in each Exam 02-19) have text-only
scenario transcriptions drawn from the companion TXT answer explanations,
chart legends and figure indexes. Answers, domains, IDs and scored/unscored
statuses have been kept from the original TXT. The rewritten questions
should receive an editorial check for ambiguity and aviation accuracy before
being distributed to customers. Do not present these as official FAA items.

INSTALL (from the project's root directory on the Mac):

  ditto -x -k "$HOME/Downloads/FAA_PART107_EXAMS_02_19_TEXT_ONLY.zip" .
  python3 tools/install_faa107_remaining.py
  git status --short

This install does NOT push or publish anything. The .gitignore already
excludes imports/, so the review register remains local.

After verifying locally and approving the transcriptions, commit ONLY:
  packs/faa-part-107/config.json
  packs/faa-part-107/data/faa-part-107_exam_{02..19}.json
  packs/faa-part-107/pdf/faa_part_107_practice_exam_{02..19}.pdf
  tools/install_faa107_remaining.py
  README_FAA_20_EXAMS.txt

Do not stage imports/ or any scratch files.
TXT originals remain intact and must not be committed.

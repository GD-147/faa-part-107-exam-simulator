FAA PART 107 REMOTE PILOT - IMPORT PACKAGE

Audited all 20 supplied TXT files without changing their contents.
- 20 tests x 65 items = 1300; every test has 60 scored, 5 unscored.
- Every scored-test distribution: Regulations 29 / Airspace 12 / Weather 3 / Loading 1 / Operations 15.
- 171 original questions referred to unavailable figures.
- Exam 01: 9 questions manually rewritten into self-contained text exercises, retaining existing correct answers and explanations.
- Exam 20: original text exhibits are self-contained; no external PNG required.
- Exams 02-19: 162 figure-dependent questions still require editorial rewrite. DO NOT PUBLISH draft files.
- Exam 01 & 20 have printable PDFs with answer keys and explanations.

FILES
 tools/import_faa107.py = repeatable strict importer for all 20 ORIGINAL TXT files (generates drafts)
 tools/install_faa107_approved.py = optional local install of ONLY exams 01 and 20; never commits/pushes
 imports/faa_review/draft_json = 20 DRAFT JSONs, including unresolved external figures (DO NOT PUBLISH)
 imports/faa_review/approved_exams = platform-ready text-only Exam 01 & 20 + printable PDFs
 imports/faa_review/figure_rewrite_registry.csv = 171 items and explanatory source context, with 9 resolved
 imports/faa_review/audit_summary.json = all exam distribution counts

MAC USE
1. Extract the zip into the root faa-part-107-exam-simulator folder.
2. Optional stage of exams 01 and 20 (not the others): python3 tools/install_faa107_approved.py
3. Review files and test locally before committing/pushing.
4. All contents in imports/ are ignored by the existing .gitignore.

No missing-question invention, no silent changes to original answer keys, and no new image assets.
Quality assurance: structurally validated, not independently re-verified against every current FAA regulation.

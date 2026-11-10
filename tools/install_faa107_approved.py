#!/usr/bin/env python3
"""Stage the text-only approved FAA practice exams 01 and 20. No git push."""
from pathlib import Path
import json, shutil, collections

root = Path(__file__).resolve().parents[1]
assert root.name == 'faa-part-107-exam-simulator', f'Wrong project directory: {root}'
cfg_path = root/'packs/faa-part-107/config.json'
logo_path = root/'packs/faa-part-107/assets/logo.png'
assert cfg_path.is_file() and logo_path.is_file(), 'Missing FAA project config or logo'
cfg = json.loads(cfg_path.read_text(encoding='utf-8'))
assert cfg.get('examId') == 'faa-part-107' and cfg.get('accessPassword') == 'FAA107PREP'
ids = [1, 20]
filenames = [f'faa-part-107_exam_{i:02d}.json' for i in ids]
existing = cfg.get('examFiles', [])
assert not existing or existing == filenames, f'Exams already configured: {existing}; refusing to overwrite'

required = {'Regulations':29,'Airspace Classification and Operating Requirements':12,'Weather':3,'Loading and Performance':1,'Operations':15}
sources = []
for i in ids:
    folder = root/'imports/faa_review/approved_exams'
    src = folder/f'faa-part-107_exam_{i:02d}.json'
    pdf = folder/f'faa_part_107_practice_exam_{i:02d}.pdf'
    assert src.is_file() and pdf.is_file(), f'Missing approved exam/PDF {i}'
    doc = json.loads(src.read_text(encoding='utf-8'))
    qs = doc['questions']
    assert doc['examId'] == 'faa-part-107' and len(qs) == 65
    assert sum(q.get('unscored') is True for q in qs) == 5
    assert sum(not q.get('unscored') for q in qs) == 60
    assert all(set(q['choices']) == {'A','B','C'} and q['correct'] in ('A','B','C') and q.get('explanation') and not q.get('requiresFigureRewrite') for q in qs)
    assert dict(collections.Counter(q['domain'] for q in qs if not q['unscored'])) == required
    sources.append((src,pdf))

counts = {'domain1':(29,58),'domain2':(12,24),'domain3':(3,6),'domain4':(1,2),'domain5':(15,30)}
assert len(cfg['sections'])==6 and cfg['sections'][-1]['id']=='full'
for sec in cfg['sections']:
    if sec['id'] in counts:
        sec['questionCount'],sec['timeMin']=counts[sec['id']]
    elif sec['id']=='full':
        assert sec['questionCount']==65 and sec['timeMin']==120 and sec['scoredCount']==60 and sec['unscoredCount']==5
cfg['examFiles']=filenames
cfg['printables']=[{'label': f'Practice Exam {i:02d} — Full-Length (Answer Key and Explanations)', 'file': f'faa_part_107_practice_exam_{i:02d}.pdf'} for i in ids]

style_path = root/'app/styles.css'
style = style_path.read_text(encoding='utf-8')
if '/* FAA TEXT EXHIBITS */' not in style:
    style+='\n/* FAA TEXT EXHIBITS */\n.questionPrompt { white-space: pre-line; }\n'
app_path=root/'app/app.html'
app=app_path.read_text(encoding='utf-8')
app=app.replace('Question sets and printable PDFs will be available after validation.', 'Choose a domain or a timed full-length test. Printable exams include an answer key and explanations.')

# Passed all checks. Install files into the new FAA project; do not touch the original repos.
datadir=root/'packs/faa-part-107/data'; pdfdir=root/'packs/faa-part-107/pdf'
datadir.mkdir(parents=True,exist_ok=True);pdfdir.mkdir(parents=True,exist_ok=True)
for src,pdf in sources:
    shutil.copy2(src,datadir/src.name)
    shutil.copy2(pdf,pdfdir/pdf.name)
cfg_path.write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
style_path.write_text(style,encoding='utf-8')
app_path.write_text(app,encoding='utf-8')
print('STAGED LOCALLY: FAA Exams 01 and 20 + two printable PDFs')
print('SIX SECTIONS: 5 domains + 65-question Full-Length')
print('DOMAIN EXAM MODE COUNTS (each test): 29 / 12 / 3 / 1 / 15')
print('PASS/FAIL: 42 / 60 scored')
print('EXAMS 02-19: DRAFT ONLY, NOT PUBLISHED')
print('GIT PUSH: NOT EXECUTED')

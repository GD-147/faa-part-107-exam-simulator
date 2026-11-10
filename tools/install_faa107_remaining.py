#!/usr/bin/env python3
"""Validate and activate 18 FAA Part 107 tests 02–19 without pushing.
Expected to be executed from the root of the faa-part-107-exam-simulator Mac checkout.
Preserves the original TXT files in imports/ and existing Exams 01 and 20.
"""
from __future__ import annotations
import collections, json, os, re
from pathlib import Path

root=Path.cwd()
assert root.name=='faa-part-107-exam-simulator', f'Wrong working directory: {root}'
base=root/'packs/faa-part-107'
config_path=base/'config.json'
config=json.loads(config_path.read_text(encoding='utf-8'))
assert config['examId']=='faa-part-107'
assert config['accessPassword']=='FAA107PREP'
assert config['practiceChunkSize']==30, 'Expected Practice Mode chunk size of 30'
assert len(config['sections'])==1 and config['sections'][0]['id']=='full'
full=config['sections'][0]
assert (full['questionCount'],full['timeMin'],full['scoredCount'],full['unscoredCount'],full['passingScore'])==(65,120,60,5,70)
assert (base/'assets/logo.png').is_file()

expected=['faa-part-107_exam_%02d.json'%n for n in range(1,21)]
initial=['faa-part-107_exam_01.json','faa-part-107_exam_20.json']
assert config['examFiles'] in (initial,expected), 'Unexpected examFiles config; review manually before install'

per_domain={'Regulations':29,'Airspace Classification and Operating Requirements':12,'Weather':3,'Loading and Performance':1,'Operations':15}
ids=set();adapted=0
for n,name in enumerate(expected,1):
    path=base/'data'/name
    assert path.is_file(),f'Missing JSON {path}'
    doc=json.loads(path.read_text(encoding='utf-8'))
    assert doc.get('examId')=='faa-part-107',name
    qs=doc.get('questions',[])
    assert len(qs)==65,(name,len(qs))
    scored=[q for q in qs if q.get('unscored') is False]
    pilot=[q for q in qs if q.get('unscored') is True]
    assert len(scored)==60 and len(pilot)==5,name
    assert collections.Counter(q['domain'] for q in scored)==per_domain,name
    for j,q in enumerate(qs,1):
        assert q['id']==f'FAA107-T{n:02d}-Q{j:03d}',(name,j,q['id'])
        assert q['id'] not in ids,q['id']
        ids.add(q['id'])
        assert set(q['choices'])=={'A','B','C'},q['id']
        assert all(isinstance(q['choices'][x],str) and q['choices'][x].strip() for x in 'ABC')
        assert q['correct'] in 'ABC'
        assert q['prompt'].strip() and q['explanation'].strip(),q['id']
        assert not q.get('requiresFigureRewrite'),q['id']
        assert not re.search(r'(?i)figures/|\.(?:png|jpg|webp)\b',q['prompt']),q['id']
        if n!=20:
            assert not re.search(r'FAA107-T\d{2}-F\d{2}',q['prompt']),q['id']
        # Exam 20 uses embedded text exhibits whose IDs are part of the self-contained question.
        adapted+=bool(q.get('textOnlyAdaptation'))
    pdf=base/'pdf'/f'faa_part_107_practice_exam_{n:02d}.pdf'
    assert pdf.is_file() and pdf.stat().st_size>20000 and pdf.open('rb').read(4)==b'%PDF',pdf
    print(f'VALID: Exam {n:02d} | 65 questions | 60 scored | 5 unscored | printable PDF')

assert len(ids)==1300,(len(ids))
assert adapted==162,('Expected precisely 162 text-only rewrite records in Exams 02-19',adapted)
assert all(not (root/'imports').resolve() in p.parents for p in [base/'config.json']), 'Path separation error'

# Existing PDF entries are reused unchanged. New entries are added in numbered order.
original_printables={}
for item in config.get('printables',[]):
    m=re.search(r'practice_exam_(\d{2})\.pdf$',item['file'],re.I)
    assert m,('Unexpected PDF entry',item)
    original_printables[int(m.group(1))]=item
assert {1,20}<=set(original_printables),'Existing PDF entries 01 and 20 are missing'
new_printables=[original_printables[n] if n in original_printables else {
    'label':f'Practice Exam {n:02d} — Full-Length (65 Questions)',
    'file':f'faa_part_107_practice_exam_{n:02d}.pdf'} for n in range(1,21)]

config['examFiles']=expected
config['printables']=new_printables
config['sections'][0]['examFiles']=[]

# Store an ignored local backup; do not touch original user TXT files.
backup=root/'imports/faa_review/config_before_20_exams.json'
backup.parent.mkdir(parents=True,exist_ok=True)
if not backup.exists():backup.write_text(config_path.read_text(encoding='utf-8'),encoding='utf-8')

tmp=config_path.with_suffix('.json.faa107tmp')
tmp.write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
os.replace(tmp,config_path)
print('======================================')
print('FAA PART 107 — 20 EXAMS READY LOCALLY')
print('======================================')
print('Full-Length tests:',len(expected))
print('Total questions:',len(ids))
print('Scored questions:',1200)
print('Simulated unscored:',100)
print('Text-only adaptations:',adapted)
print('Printable PDFs:',len(new_printables))
print('Practice Mode: 30-question progressive blocks, cumulative pool')
print('Exam Mode: 65 questions, 120 minutes, pass at 42/60 scored')
print('Original imports TXT: unchanged')
print('Git push: NOT EXECUTED')

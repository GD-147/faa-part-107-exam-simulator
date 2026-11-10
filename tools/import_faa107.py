#!/usr/bin/env python3
"""FAA Part 107 TXT -> audited draft JSON, no guesses or content changes."""
from __future__ import annotations
import csv,json,re,sys,collections
from pathlib import Path

EXAM_RE=re.compile(r'FAA_Part107_Test_(\d{2})_Complete\.txt$',re.I)
Q_RE=re.compile(r'^\s*(\d{1,2})\.\s+\[?(FAA107-T\d{2}-Q\d{3})\]?(?:\s+.*)?$',re.I)
OPTION_RE=re.compile(r'^\s*([ABC])\.\s*(.*)$')
SIMPLE_META=re.compile(r'^\s*(\d{1,2})\.\s+([ABC])\s*\|\s*(SCORED|SIMULATED VALIDATION\s*-\s*UNSCORED)\s*\|\s*(.+?)\s*$',re.I)
NEW_META=re.compile(r'^\s*(\d{1,2})\.\s+([ABC])\s*\|\s*(Scored|Unscored)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*(FAA107-T\d{2}-Q\d{3})\s*$',re.I)
MID_META=re.compile(r'^\s*(FAA107-T\d{2}-Q\d{3})\s*\|\s*([ABC])\s*\|\s*(Scored|Unscored)\s*$',re.I)
SOL_1=re.compile(r'^\s*(\d{1,2})\.\s+\[(FAA107-T\d{2}-Q\d{3})\]\s+CORRECT:\s*([ABC])\s*$',re.I)
SOL_NEW=re.compile(r'^\s*(\d{1,2})\.\s+\[(FAA107-T\d{2}-Q\d{3})\]\s+(.+?)\s*$',re.I)
NORMAL_DOMAINS={
 'regulations':'Regulations','airspace and requirements':'Airspace Classification and Operating Requirements',
 'airspace classification and operating requirements':'Airspace Classification and Operating Requirements',
 'weather':'Weather','loading and performance':'Loading and Performance','operations':'Operations',
}
FILE_RE=re.compile(r'(?i)\b(?:figure\s*(?:file)?|image|exhibit)\s*:\s*\S+\.(?:png|jpe?g|webp)\b')
EXTERNAL_REF=re.compile(r'(?i)(?:\b(?:refer\s+to|use|review|inspect|in|from|according\s+to)\s+(?:the\s+)?(?:figure|fig\.?|exhibit)\b|\b(?:figure|fig\.?|exhibit)\s*FAA107-T\d{2}-F\d{2}\b|\b(?:refer\s+to|use)\s+F0[1-9]\b)')
STARTS=re.compile(r'(?im)^\s*QUESTIONS\s*$')
ENDERS=re.compile(r'(?im)^\s*(?:END OF LEARNER TEST|FIGURE INDEX|END OF CANDIDATE QUESTIONS|END OF QUESTIONS)\s*$')

def tidy(s):
 return re.sub(r'[ \t]+',' ',s).strip()
def collapse(lines):
 return '\n'.join(s.strip() for s in lines).strip()

def read_one(p):
 text=p.read_text(encoding='utf-8-sig')
 lines=text.splitlines()
 match=EXAM_RE.search(p.name)
 assert match, p.name
 n=int(match.group(1))
 # Question range
 st=[i for i,x in enumerate(lines) if x.strip().upper()=='QUESTIONS']
 if len(st)!=1: raise ValueError(f'{p.name}: QUESTIONS heading count {len(st)}')
 start=st[0]+1
 ed=[i for i,x in enumerate(lines[start:],start) if ENDERS.match(x)]
 if not ed: raise ValueError(f'{p.name}: question end marker missing')
 end=ed[0]
 q_heads=[(i,int(m.group(1)),m.group(2)) for i in range(start,end) if (m:=Q_RE.match(lines[i]))]
 if len(q_heads)!=65:
  raise ValueError(f'{p.name}: expected 65 question headers, found {len(q_heads)} ({q_heads[:3]})')
 questions={}
 for ix,(i,num,id_) in enumerate(q_heads):
  stop=q_heads[ix+1][0] if ix<64 else end
  body=lines[i+1:stop]
  # in 01 last question ended by marker, others captions between q chunks
  choices={}
  first=[]
  current=None
  for line in body:
   mo=OPTION_RE.match(line)
   if mo and mo.group(1) not in choices:
    current=mo.group(1)
    choices[current]=[mo.group(2)]
   elif current:
    choices[current].append(line)
   else:
    first.append(line)
  if set(choices)!=set('ABC'):
   raise ValueError(f'{p.name} Q{num:02d}: choices {list(choices)}')
  prompt=collapse(first)
  choices={k:tidy(' '.join(v)) for k,v in choices.items()}
  if not prompt or any(not v for v in choices.values()):
   raise ValueError(f'{p.name} Q{num:02d}: empty prompt or choice')
  if id_.upper()!=f'FAA107-T{n:02d}-Q{num:03d}':
   raise ValueError(f'{p.name} Q{num}: ID mismatch {id_}')
  questions[num]={'id':id_.upper(),'prompt':prompt,'choices':choices}
 # Metadata
 metadata={}
 if n==1:
  for line in lines[end+1:]:
   m=SIMPLE_META.match(line)
   if m:
    no=int(m.group(1)); metadata[no]=(m.group(2).upper(), 'UNSCORED' in m.group(3).upper(), tidy(m.group(4)))
 elif 2<=n<=15:
  for i,line in enumerate(lines):
   m=MID_META.match(line)
   if m:
    id_=m.group(1).upper(); no=int(id_.rsplit('-Q',1)[-1]);
    meta=next((ln.strip() for ln in lines[i+1:i+4] if ' | ' in ln and not MID_META.match(ln)),None)
    if not meta: raise ValueError(f'{p.name} Q{no}: no domain metadata')
    domain=tidy(meta.split('|',1)[0])
    metadata[no]=(m.group(2).upper(),m.group(3).lower()=='unscored',domain)
 else:
  for line in lines[end+1:]:
   m=NEW_META.match(line)
   if m:
    no=int(m.group(1)); id_=m.group(6).upper();
    if id_!=f'FAA107-T{n:02d}-Q{no:03d}':raise ValueError(f'{p.name} Q{no} metadata ID mismatch')
    metadata[no]=(m.group(2).upper(),m.group(3).lower()=='unscored',tidy(m.group(4)))
 if len(metadata)!=65:
  raise ValueError(f'{p.name}: expected 65 scoring metadata records, got {len(metadata)}: {list(metadata)[:10]}')
 # explanation blocks
 explanation={};ex_keys={}
 if n==1:
  heads=[(i,int(m.group(1)),m.group(2).upper(),m.group(3).upper()) for i,line in enumerate(lines[end+1:],end+1) if (m:=SOL_1.match(line))]
  if len(heads)!=65:raise ValueError(f'{p.name}: expected 65 solution headers, got {len(heads)}')
  for z,(idx,no,id_,ans) in enumerate(heads):
   stop=heads[z+1][0] if z<len(heads)-1 else next((i for i in range(idx+1,len(lines)) if lines[i].upper().startswith('AUTHORING AND SCORING NOTES')),len(lines))
   explanation[no]=collapse(lines[idx+1:stop]); ex_keys[no]=ans
 elif 2<=n<=15:
  heads=[(i,int(m.group(1).upper().rsplit('-Q',1)[-1]),m.group(2).upper()) for i,line in enumerate(lines) if (m:=MID_META.match(line))]
  for z,(idx,no,ans) in enumerate(heads):
   stop=heads[z+1][0] if z<len(heads)-1 else len(lines)
   block=lines[idx+2:stop]  # exclude domain metadata line
   # stop before editorial notes if present
   for k,line in enumerate(block):
    if re.match(r'^\s*(?:EXAM FORMAT SOURCES|AUTHORING|QUALITY|SCORING|REVIEW|END OF ANSWER|CONSTRUCTION|TEST DEVELOPMENT)\b',line,re.I):
     block=block[:k];break
   explanation[no]=collapse(block); ex_keys[no]=ans
 else:
  # Can include multiple other occurrences of ID; restrict headings after metadata
  body_start=next((i for i,line in enumerate(lines) if re.match(r'^\s*(?:EXPLANATIONS AND VERIFIABLE REFERENCES|DETAILED SOLUTIONS AND DISTRACTOR ANALYSIS)',line,re.I)),len(lines))
  heads=[(i,int(m.group(1)),m.group(2).upper(),m.group(3)) for i,line in enumerate(lines[body_start+1:],body_start+1) if (m:=SOL_NEW.match(line))]
  if len(heads)!=65:raise ValueError(f'{p.name}: expected 65 solution headers, found {len(heads)}')
  for z,(idx,no,id_,headline) in enumerate(heads):
   stop=heads[z+1][0] if z<len(heads)-1 else len(lines)
   block=lines[idx+1:stop]
   for k,line in enumerate(block):
    if re.match(r'^\s*(?:FIGURE DIRECTORY AND PROVENANCE|EXHIBIT PROVENANCE|FORM SPECIFICATIONS|SERIES COMPARISON NOTE|EDITORIAL|AUTHORING|QA NOTES|SCORING AND|TECHNICAL NOTES)',line,re.I):block=block[:k];break
   explanation[no]=collapse(block)
   m=re.search(r'(?i)\bCorrect answer\s*:?\s*([ABC])\b',headline)
   if not m:
    m=re.search(r'(?im)^\s*Correct(?:\s+answer)?\s*:?\s*([ABC])\b',explanation[no])
   if m:ex_keys[no]=m.group(1).upper()
 for no in range(1,66):
  if no not in questions or no not in metadata or no not in explanation:
   raise ValueError(f'{p.name} missing Q{no} in data')
  ans,unscored,rawdomain=metadata[no]
  q=questions[no]
  if not q['choices'].get(ans):raise ValueError(f'{p.name} Q{no} answer {ans} not a choice')
  if no in ex_keys and ex_keys[no]!=ans:
   raise ValueError(f'{p.name} Q{no} answer conflict: metadata {ans}, explanation {ex_keys[no]}')
  norm=NORMAL_DOMAINS.get(rawdomain.lower())
  if not norm:raise ValueError(f'{p.name} Q{no}: unknown domain {rawdomain}')
  q.update({'domain':norm,'correct':ans,'unscored':unscored,'explanation':explanation[no]})
  # Embed Exhibit 20 textual data, remove distracting figure ID etc? leave embedded exhibit text (self-contained)
  # Detect external assets references, including variants that do not use explicit file marker
  ptxt=q['prompt']
  files=FILE_RE.findall(ptxt)
  nontextfigure = bool(re.search(r'(?i)\bfigure\s*(?:file)?\s*:\s*(?:figures/)?\S+\.(?:png|jpg|jpeg|webp)',ptxt))
  refs=bool(EXTERNAL_REF.search(ptxt))
  embedded=bool(re.search(r'(?im)^\s*EXHIBIT\s+FAA107-T20-F\d{2}\s*[—–-]\s*',ptxt))
  # If exhibits embedded with data, distinguish from external png
  needs=nontextfigure or (refs and not embedded)
  # Retain raw path as well for editor references, flag, do not publish.
  q['requiresFigureRewrite']=bool(needs)
  if needs:
   q['reviewNote']='External figure or chart referenced; rewrite prompt, all necessary choices, and explanation into a self-contained item before publishing.'
 if len([q for q in questions.values() if q['unscored']])!=5:
  raise ValueError(f'{p.name}: expected 5 unscored, found {sum(q["unscored"] for q in questions.values())}')
 if sum(not q['unscored'] for q in questions.values())!=60:
  raise ValueError(f'{p.name}: scored not 60')
 return n,[questions[i] for i in range(1,66)]

def main():
 if len(sys.argv)!=3:print('usage: python3 import_faa107.py IMPORTS_DIR OUTPUT_DIR');return 2
 source=Path(sys.argv[1]); out=Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
 files=sorted(p for p in source.glob('FAA_Part107_Test_*_Complete.txt') if EXAM_RE.search(p.name))
 print('INPUT FILES:',len(files))
 if len(files)!=20:raise ValueError(f'Expected 20 files, found {len(files)}')
 drafts=out/'draft_json';drafts.mkdir(exist_ok=True)
 report=out/'figure_rewrite_review.csv'
 rows=[]; summary=[]
 for p in files:
  n,questions=read_one(p)
  counted=collections.Counter(q['domain'] for q in questions if not q['unscored'])
  blocked=[q for q in questions if q['requiresFigureRewrite']]
  summary.append({'exam':n,'questions':len(questions),'scored':sum(not q['unscored'] for q in questions),'unscored':sum(q['unscored'] for q in questions),'figure_rewrites':len(blocked),'scored_domains':dict(counted)})
  for q in blocked:
   rows.append({'exam':n,'id':q['id'],'domain':q['domain'],'unscored':q['unscored'],'correct':q['correct'],'prompt':q['prompt'],'A':q['choices']['A'],'B':q['choices']['B'],'C':q['choices']['C'],'explanation':q['explanation'],'reviewNote':q['reviewNote']})
  dst=drafts/f'faa-part-107_exam_{n:02d}.json';dst.write_text(json.dumps({'examId':'faa-part-107','questions':questions},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
  print(f'Exam {n:02d}: 65/60/5 VALID | images requiring rewrite: {len(blocked)} | scored domains: {dict(counted)}')
 with report.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['exam','id','domain','unscored','correct','prompt','A','B','C','explanation','reviewNote']);w.writeheader();w.writerows(rows)
 (out/'audit_summary.json').write_text(json.dumps({'totalExams':len(summary),'totalQuestions':sum(s['questions'] for s in summary),'totalFigureRewrites':len(rows),'exams':summary},indent=2,ensure_ascii=False)+'\n')
 print('NEEDS FIGURE REWRITE',len(rows))
 print('AUDIT REPORT:',report)
 return 0
if __name__=='__main__':raise SystemExit(main())

"""Refresh only verified publisher records; retain raw HTML for audit."""
import json, re, time, hashlib
from pathlib import Path
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://ajnm.samipubco.com/'
ISSUES = ['issue_33805_34320.html','issue_33805_34115.html','issue_33805_33806.html','issue_31494_33448.html','issue_31494_32093.html','issue_31494_31746.html','issue_31494_31495.html']
raw = ROOT / 'sources'
raw.mkdir(exist_ok=True)
def fetch(name):
    path = raw / name
    if path.exists(): return path.read_text(encoding='utf-8')
    with urlopen(Request(BASE+name,headers={'User-Agent':'Mozilla/5.0'}),timeout=45) as r:
        body=r.read().decode('utf-8')
    path.write_text(body,encoding='utf-8')
    time.sleep(.2)
    return body

records={}
issues=[]
for issue in ISSUES:
    body=fetch(issue)
    ids=sorted(set(re.findall(r'article_(\d+)\.html',body)))
    group=[]
    for aid in ids:
        s=BeautifulSoup(fetch('article_'+aid+'.html'),'html.parser')
        metas={}
        for m in s.select('meta[name][content]'):
            metas.setdefault(m['name'],[]).append(m['content'])
        def get(k): return metas.get(k,[''])[0].strip()
        if not get('citation_title'): raise ValueError('Missing metadata: '+aid)
        a={'id':aid,'title':get('citation_title'),'authors':metas.get('citation_author',[]),'journal':get('citation_journal_title'),'date':get('citation_date') or get('citation_publication_date'),'volume':get('citation_volume'),'issue':get('citation_issue'),'firstpage':get('citation_firstpage'),'lastpage':get('citation_lastpage'),'doi':get('citation_doi'),'pdf':get('citation_pdf_url'),'abstract':get('citation_abstract'),'keywords':[k.strip() for k in get('keywords').split(',') if k.strip()],'source':BASE+'article_'+aid+'.html','source_issue':BASE+issue,'issn':get('citation_issn'),'publisher':get('citation_publisher'),'retrieved':'2026-11-22','source_sha256':hashlib.sha256((raw/('article_'+aid+'.html')).read_bytes()).hexdigest()}
        records[aid]=a
        group.append(aid)
    issues.append({'source':BASE+issue,'articles':group})
    print(issue,len(group),flush=True)
(ROOT/'data').mkdir(exist_ok=True)
(ROOT/'data'/'articles.json').write_text(json.dumps(list(records.values()),ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'data'/'issues.json').write_text(json.dumps(issues,indent=2),encoding='utf-8')
print('Total:',len(records))

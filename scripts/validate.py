"""Verify local navigation, metadata and issue membership against source snapshots."""
import json, re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs'
records=json.loads((ROOT/'data/articles.json').read_text(encoding='utf-8'))
issues=json.loads((ROOT/'data/issues.json').read_text(encoding='utf-8'))
class Parser(HTMLParser):
    def __init__(self): super().__init__(); self.links=[];self.meta=[];self.h1=0
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if tag=='h1': self.h1+=1
        if tag=='meta': self.meta.append(d)
        for key in ('href','src','action'):
            if key in d: self.links.append(d[key])
errors=[]
for p in OUT.rglob('*.html'):
    parser=Parser();parser.feed(p.read_text(encoding='utf-8'))
    if parser.h1!=1: errors.append(f'{p}: expected one h1')
    for url in parser.links:
        split=urlsplit(url)
        if split.scheme or split.netloc or not split.path: continue
        target=(p.parent/unquote(split.path)).resolve()
        if not target.is_relative_to(OUT.resolve()) or not target.exists(): errors.append(f'{p}: missing {url}')
for a in records:
    parser=Parser();parser.feed((OUT/'articles'/f'{a["id"]}.html').read_text(encoding='utf-8'))
    pairs=[(m.get('name'),m.get('content')) for m in parser.meta]
    for key,value in [('citation_title',a['title']),('citation_doi',a['doi']),('citation_journal_title',a['journal']),('citation_pdf_url',a['pdf'])]:
        if (key,value) not in pairs: errors.append(f'{a["id"]}: incorrect {key}')
    for author in a['authors']:
        if ('citation_author',author) not in pairs: errors.append('Missing author')
    source=(ROOT/'sources'/f'article_{a["id"]}.html').read_text(encoding='utf-8')
    if a['doi'] not in source: errors.append('DOI absent from source')
for issue in issues:
    original=(ROOT/'sources'/issue['source'].rsplit('/',1)[-1]).read_text(encoding='utf-8')
    ids=set(re.findall(r'article_(\d+)\.html',original))
    if ids!=set(issue['articles']): errors.append('Issue membership differs')
if errors: raise SystemExit('\n'.join(errors))
print(f'PASS: {len(list(OUT.rglob("*.html")))} HTML pages; {len(records)} article metadata records; {len(issues)} source issue memberships; all local links.')

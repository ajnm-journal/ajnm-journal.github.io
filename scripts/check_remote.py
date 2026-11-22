"""Check real remote targets without downloading entire PDFs."""
import json
from pathlib import Path
from urllib.request import Request,urlopen
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parents[1]
A=json.loads((ROOT/'data/articles.json').read_text(encoding='utf-8'))
def check(a):
    result={'id':a['id']}
    for kind,url in [('pdf',a['pdf']),('doi','https://doi.org/'+a['doi'])]:
        try:
            with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=25) as r:
                prefix=r.read(8)
                result[kind]={'status':r.status,'final_url':r.url,'pdf_signature':prefix.startswith(b'%PDF-') if kind=='pdf' else None}
        except Exception as e: result[kind]={'error':str(e)}
    return result
with ThreadPoolExecutor(max_workers=3) as pool:
    results=list(pool.map(check,A))
(ROOT/'data/link-checks.json').write_text(json.dumps({'checked':'2026-11-22','results':results},indent=2),encoding='utf-8')
print('PDF valid:',sum(r['pdf'].get('pdf_signature',False) for r in results),'/',len(A))
print('DOI resolved:',sum(r['doi'].get('status')==200 for r in results),'/',len(A))
print('Failures:',json.dumps([r for r in results if 'error' in r['doi'] or 'error' in r['pdf']]))

"""Build a portable static archive using only the Python standard library."""
import json, html, os, re
from pathlib import Path
from collections import defaultdict
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs'
OUT.mkdir(exist_ok=True)
A=json.loads((ROOT/'data/articles.json').read_text(encoding='utf-8'))
TITLE='Advanced Journal of Nanomaterials'
BASE=os.environ.get('SITE_URL','').rstrip('/')
if BASE and (urlparse(BASE).scheme!='https' or not urlparse(BASE).netloc):
    raise ValueError('SITE_URL must be a full HTTPS URL')
E=lambda v:html.escape(str(v),quote=True)
groups=defaultdict(list)
for a in A:
    for k in ('id','title','authors','journal','volume','issue','doi','pdf','date'):
        if not a[k]: raise ValueError(f'Missing {k}: {a["id"]}')
    if not re.fullmatch(r'\d+',a['id']): raise ValueError('Invalid ID')
    if not re.fullmatch(r'10\.\d{4,9}/\S+',a['doi']): raise ValueError('Invalid DOI')
    if not a['pdf'].startswith('https://ajnm.samipubco.com/'): raise ValueError('Unexpected PDF host')
    groups[(a['volume'],a['issue'])].append(a)
assert len({a['id'] for a in A})==len(A)
assert len({a['doi'].lower() for a in A})==len(A)
keys=sorted(groups,key=lambda k:tuple(map(int,k)),reverse=True)
for g in groups.values(): g.sort(key=lambda a:int(a['firstpage'] or 0))
latest=keys[0]
def issuepath(k): return f'issues/volume-{k[0]}-issue-{k[1]}.html'
def page(path,title,body,meta='',depth=0,active=''):
    pre='../'*depth
    nav=''.join(f'<a {"aria-current=\"page\"" if active==label else ""} href="{pre}{link}">{label}</a>' for label,link in [('Home','index.html'),('Archives','archives.html'),('All articles','articles.html'),('Search','search.html'),('About','about.html')])
    canonical=f'<link rel="canonical" href="{E(BASE+"/"+path)}">' if BASE else ''
    output=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{E(title)} | AJNM Repository</title><meta name="description" content="{E(title)} — AJNM scholarly article archive, with publisher metadata, DOI and full-text links.">{canonical}{meta}<link rel="stylesheet" href="{pre}assets/style.css"><script defer src="{pre}assets/search.js"></script></head><body><a class="skip" href="#main">Skip to content</a><header><div class="brand"><a class="monogram" href="{pre}index.html" aria-label="AJNM home">AJNM<span>REPOSITORY</span></a><div><p class="eyebrow">SAMI PUBLISHING COMPANY · SCHOLARLY ARCHIVE</p><p class="brand-name">{TITLE}</p></div></div><nav aria-label="Main navigation">{nav}<a href="https://ajnm.samipubco.com/">Publisher website</a></nav></header><main id="main">{body}</main><footer><strong>AJNM · Research, connected.</strong><p>Article records from <a href="https://ajnm.samipubco.com/">the publisher</a>. Snapshot: 22 November 2026. PDF files remain on the publisher website.</p><p><a href="{pre}about.html">Sources & naming note</a> · <a href="{pre}data/articles.json">Download metadata (JSON)</a></p></footer></body></html>'''
    p=OUT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(output,encoding='utf-8')
def card(a,pre=''):
    hay=' '.join([a['title'],*a['authors'],*a['keywords'],a['doi']])
    return f'''<article class="record" data-search="{E(hay)}" data-year="{E(a['date'][:4])}" data-volume="{E(a['volume'])}"><div class="record-meta">{E(a['date'][:4])} · Volume {E(a['volume'])} · Issue {E(a['issue'])} · pp. {E(a['firstpage'])}–{E(a['lastpage'])}</div><h2><a href="{pre}articles/{a['id']}.html">{E(a['title'])}</a></h2><p class="authors">{E('; '.join(a['authors']))}</p><div class="record-links"><a href="https://doi.org/{E(a['doi'])}">DOI: {E(a['doi'])}</a><a href="{E(a['pdf'])}">Full-text PDF</a></div></article>'''
def groupcard(k):
    aa=groups[k]
    return f'<a class="issue-card" href="{issuepath(k)}"><span class="eyebrow">{E(aa[0]["date"][:4])} · VOLUME {k[0]}</span><h3>Issue {k[1]}</h3><p>{len(aa)} articles · pp. {aa[0]["firstpage"]}–{aa[-1]["lastpage"]}</p><span class="issue-link">Browse issue</span></a>'
stats=f'<div class="stats"><div><strong>{len(set(a["volume"] for a in A))}</strong><span>Volumes</span></div><div><strong>{len(groups)}</strong><span>Issues</span></div><div><strong>{len(A)}</strong><span>Article records</span></div><div><strong>2025–2026</strong><span>Publication years</span></div></div>'
hero=f'''<section class="hero"><div><p class="eyebrow">AJNM / OPEN RESEARCH COLLECTION</p><h1>Explore the science.<br><em>Discover the connections.</em></h1><p class="intro">Browse published research, find an article, and follow its DOI to the original scholarly record.</p><form action="search.html" class="hero-search"><label for="home-query">Search the archive</label><div class="search-row"><input id="home-query" name="q" type="search" placeholder="Title, author, keyword or DOI"><button>Search</button></div></form><a class="text-link" href="archives.html">Browse volumes and issues</a></div><div class="orb" aria-hidden="true"><div class="orbit o1"></div><div class="orbit o2"></div><div class="orbit o3"></div><span class="core">AJNM</span><span class="orb-caption">NANOSCALE SCIENCE<br>CONNECTED KNOWLEDGE</span></div></section>'''
page('index.html',TITLE,hero+stats+f'<section class="section"><div class="section-title"><div><p class="eyebrow">LATEST ARCHIVED ISSUE</p><h2>Volume {latest[0]} · Issue {latest[1]}</h2></div><a href="{issuepath(latest)}">View all {len(groups[latest])} articles</a></div>'+''.join(card(a) for a in groups[latest][:3])+'</section><section class="section"><div class="section-title"><h2>The archive</h2><a href="archives.html">All volumes</a></div><div class="issue-grid">'+''.join(groupcard(k) for k in keys[:3])+'</div></section><aside class="note">Repository display title: Advanced Journal of Nanomaterials. Source records identify the journal as Advanced Journal of Nanochemistry and Medicine. <a href="about.html">Read the naming note</a>.</aside>',active='Home')
archive='<p class="eyebrow">BROWSE THE COLLECTION</p><h1>Volumes & issues</h1><p class="intro">Browse the seven published issues captured from the publisher archive.</p>'
for v in sorted(set(a['volume'] for a in A),key=int,reverse=True):
    kk=[k for k in keys if k[0]==v]
    archive+=f'<section class="section"><h2>Volume {v} <span class="muted">/ {groups[kk[0]][0]["date"][:4]}</span></h2><div class="issue-grid">'+''.join(groupcard(k) for k in kk)+'</div></section>'
page('archives.html','Volumes & issues',archive,active='Archives')
ordered=[a for k in keys for a in groups[k]]
page('articles.html','All articles','<p class="eyebrow">THE COMPLETE SNAPSHOT</p><h1>All articles</h1><p class="intro">'+str(len(A))+' publisher records, ordered by volume, issue and page.</p>'+''.join(card(a) for a in ordered),active='All articles')
controls='''<form id="search-form" class="search-panel" role="search"><label for="query">Title, author, keyword or DOI</label><div class="search-row"><input id="query" name="q" type="search" placeholder="Search all article records"><button type="submit">Search</button></div><div class="filters"><label>Year <select id="year"><option value="">All years</option><option>2026</option><option>2025</option></select></label><label>Volume <select id="volume"><option value="">All volumes</option><option>2</option><option>1</option></select></label><button type="reset" class="secondary">Clear filters</button></div></form><p id="result-count" role="status" aria-live="polite"></p><p id="empty" hidden>No articles match your search. Try fewer words or clear the filters.</p><noscript><p>Interactive search requires JavaScript. All article records are listed below; use your browser’s Find command.</p></noscript>'''
page('search.html','Search articles','<p class="eyebrow">FIND A PUBLICATION</p><h1>Search the archive</h1>'+controls+'<section id="results" aria-label="Search results">'+''.join(card(a) for a in ordered)+'</section>',active='Search')
for k in keys:
    aa=groups[k]
    page(issuepath(k),f'Volume {k[0]}, Issue {k[1]}',f'<p class="breadcrumb"><a href="../archives.html">Archives</a> / Volume {k[0]}</p><p class="eyebrow">{aa[0]["date"][:4]} · {len(aa)} ARTICLES</p><h1>Volume {k[0]} · Issue {k[1]}</h1><p><a href="{E(aa[0]["source_issue"])}">View publisher issue</a></p>'+''.join(card(a,'../') for a in aa),depth=1)
for a in A:
    k=(a['volume'],a['issue'])
    pairs={'citation_title':a['title'],'citation_journal_title':a['journal'],'citation_publication_date':a['date'],'citation_volume':a['volume'],'citation_issue':a['issue'],'citation_firstpage':a['firstpage'],'citation_lastpage':a['lastpage'],'citation_doi':a['doi'],'citation_pdf_url':a['pdf'],'citation_issn':a['issn'],'citation_publisher':a['publisher']}
    meta=''.join(f'<meta name="{key}" content="{E(val)}">' for key,val in pairs.items() if val)+''.join(f'<meta name="citation_author" content="{E(author)}">' for author in a['authors'])
    ld={'@context':'https://schema.org','@type':'ScholarlyArticle','headline':a['title'],'author':[{'@type':'Person','name':x} for x in a['authors']],'datePublished':a['date'].replace('/','-'),'identifier':a['doi'],'sameAs':a['source'],'isPartOf':{'@type':'PublicationIssue','issueNumber':a['issue'],'isPartOf':{'@type':'PublicationVolume','volumeNumber':a['volume'],'isPartOf':{'@type':'Periodical','name':a['journal'],'issn':a['issn']}}},'encoding':{'@type':'MediaObject','contentUrl':a['pdf'],'encodingFormat':'application/pdf'},'keywords':a['keywords']}
    meta+='<script type="application/ld+json">'+json.dumps(ld,ensure_ascii=False).replace('<','\\u003c')+'</script>'
    citation=f'{"; ".join(a["authors"])}. {a["title"]}. {a["journal"]}. {a["date"][:4]}; {a["volume"]}({a["issue"]}): {a["firstpage"]}–{a["lastpage"]}. https://doi.org/{a["doi"]}'
    body=f'''<p class="breadcrumb"><a href="../archives.html">Archives</a> / <a href="../{issuepath(k)}">Volume {k[0]} · Issue {k[1]}</a></p><p class="eyebrow">ARTICLE RECORD · {E(a['date'])} · PP. {E(a['firstpage'])}–{E(a['lastpage'])}</p><h1 class="article-title">{E(a['title'])}</h1><p class="article-authors">{E('; '.join(a['authors']))}</p><div class="actions"><a class="button" href="{E(a['pdf'])}">Read full-text PDF</a><a class="button secondary" href="https://doi.org/{E(a['doi'])}">Resolve DOI</a><a href="{E(a['source'])}">Publisher record</a></div><div class="article-layout"><section><h2>Abstract</h2><p class="abstract">{E(a['abstract']) or 'No abstract supplied by the publisher.'}</p><h2>Keywords</h2><div class="tags">{''.join('<span>'+E(t)+'</span>' for t in a['keywords'])}</div><h2>Cite this article</h2><p class="citation">{E(citation)}</p></section><aside class="details"><h2>Publication details</h2><dl><dt>Journal in source record</dt><dd>{E(a['journal'])}</dd><dt>Publisher</dt><dd>{E(a['publisher'])}</dd><dt>Volume / Issue</dt><dd>{k[0]} / {k[1]}</dd><dt>Publication date</dt><dd>{E(a['date'])}</dd><dt>DOI</dt><dd><a href="https://doi.org/{E(a['doi'])}">{E(a['doi'])}</a></dd><dt>Source checked</dt><dd>22 November 2026</dd></dl><p>Bibliographic values are reproduced from the publisher. Full text is hosted by the publisher.</p></aside></div>'''
    page('articles/'+a['id']+'.html',a['title'],body,meta,1)
page('about.html','About this repository','''<p class="eyebrow">PROVENANCE & SCOPE</p><h1>About the AJNM repository</h1><div class="prose"><h2>A connected scholarly archive</h2><p>This independent repository presents article metadata from <a href="https://ajnm.samipubco.com/">AJNM’s publisher website</a>, with links to the original DOI and full-text PDF. It includes the seven published issues in Volumes 1 and 2, retrieved on 22 November 2026. Articles in press are outside this snapshot.</p><h2>A note on the journal name</h2><p>At the repository owner’s request, this website uses <strong>Advanced Journal of Nanomaterials</strong> as its display title. The publisher website and the harvested article metadata use <strong>Advanced Journal of Nanochemistry and Medicine</strong>. Citation metadata and references preserve the source title. This repository does not assert that a formal journal title change has occurred.</p><h2>Source and reuse</h2><p>Article titles, authors, abstracts, keywords, dates, pagination, DOI and PDF URLs are transcribed from the publisher’s article pages. Each record includes its original source URL and retrieval date. The publisher describes published articles as <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>; consult each original article for specific credits and third-party material. Text has been converted to plain text for display; scholarly content has not been rewritten.</p><h2>Coverage and preservation</h2><p>Counts on this site are calculated from imported records, rather than copied from changing journal statistics. PDF links point to the publisher; this repository does not store PDF copies and is not a long-term full-text preservation service.</p><h2>Corrections</h2><p>For changes to the scholarly record, use the <a href="https://ajnm.samipubco.com/journal/contact.us">publisher contact page</a>. Update this repository only after checking the source record.</p></div>''',active='About')
page('404.html','Page not found','<h1>Page not found</h1><p>This record may have moved. Return to the repository home address or use the archive navigation.</p>')
(OUT/'.nojekyll').touch()
(OUT/'data').mkdir(exist_ok=True)
(OUT/'data/articles.json').write_text(json.dumps(A,ensure_ascii=False,indent=2),encoding='utf-8')
if BASE:
    urls=[p.relative_to(OUT).as_posix() for p in OUT.rglob('*.html') if p.name!='404.html']
    (OUT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+E(BASE+'/'+u)+'</loc></url>' for u in urls)+'</urlset>',encoding='utf-8')
    (OUT/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+BASE+'/sitemap.xml\n',encoding='utf-8')
print(f'Built {len(A)} articles, {len(groups)} issues in {OUT}')

"""The count behind the experiment "WE Counted Its First 272 Posts" (25 November 2026).

    python scripts/selfaudit.py

Counts things in the posts folder: kinds, headline patterns, subject tags,
lengths, endings, repeated phrases and the state of the bets. It reads
nothing with a model and judges nothing. Run it again later and compare.
"""
import importlib.util, sys, os, re, json, pathlib, collections, statistics
sys.path.insert(0,'agent'); os.environ['ANTHROPIC_API_KEY']='x'
spec = importlib.util.spec_from_file_location('agent','agent/agent.py'); A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A)
posts=[]
for f in sorted(pathlib.Path('src/posts').glob('*.md')):
    t=f.read_text(); fm,body=t.split('\n---\n',1)
    if f.name[:10] > '2026-11-25': continue
    form=(re.search(r'^form: (\w+)',fm,re.M) or [0,'response'])[1]
    if form in ('heresy','satire'): continue
    conv=bool(re.search(r'^provenance:\s*"?conversation',fm,re.M))
    title=re.search(r'^title: "(.*)"',fm,re.M).group(1)
    tags=re.search(r'^tags: \[(.*)\]',fm,re.M); tags=[x.strip() for x in tags.group(1).split(',')] if tags else []
    posts.append(dict(f=f.name,date=f.name[:10],form=form,conv=conv,title=title,tags=tags,body=body,rt='responds_to:' in fm))
print('posts',len(posts), 'from',posts[0]['date'],'to',posts[-1]['date'])
c=collections.Counter(p['form'] for p in posts); print(c)
news=[p for p in posts if p['form']=='response' and p['rt']]
print('news replies (with responds_to):',len(news))
form_hits=[p for p in news if A.check_title_formula(p['title'])]
print('headline formula:',len(form_hits),'of',len(news), round(100*len(form_hits)/len(news)))
nov=[p for p in news if p['date']>='2026-11-01']; print('nov news',len(nov),'formula',sum(1 for p in nov if A.check_title_formula(p['title'])))
verbs=collections.Counter()
for p in news:
    v=p['title'].rsplit("'",1)[-1]
    m=re.search(r"\b(Has|Is Missing|Gets|Got|Finds|Buries|Is Asking|Sends|Stops)\b",v)
    if m: verbs[m.group(1)]+=1
print(verbs.most_common())
# word counts
wc=[A.visible_words(p['body']) for p in news]; print('news words median',statistics.median(wc),'share 450-650',round(100*sum(1 for w in wc if 450<=w<=650)/len(wc)))
# who is named
def cnt(pat,ps): return sum(1 for p in ps if re.search(pat,p['body']))
for name,pat in [('regulator-ish (ICO|FCA|Ofcom|CMA|regulator)',r'\b(ICO|FCA|Ofcom|CMA|regulators?)\b'),('own/owner/ownership',r'\b(own(s|ed|er|ers|ership)?)\b'),('vote',r'\bvotes?\b'),('dividend',r'\bdividends?\b')]:
    print(name, cnt(pat,news),'of',len(news), '| nov',cnt(pat,nov),'of',len(nov))
# ownership tag by month, all posts excluding how_to
for m in ['2026-08','2026-09','2026-10','2026-11']:
    ps=[p for p in posts if p['date'].startswith(m) and p['form']!='how_to']
    print(m,len(ps),'ownership-tagged',sum(1 for p in ps if 'ownership' in p['tags']), 'rules-tagged',sum(1 for p in ps if 'rules' in p['tags']))
# last sentences
def last(body):
    s=[x.strip() for x in re.split(r'(?<=[.!?])\s+',A.plain_text(body).strip()) if x.strip()]
    return s[-1] if s else ''
ls=[len(last(p['body']).split()) for p in news]; print('last sentence median words',statistics.median(ls),'share <=8 words',round(100*sum(1 for x in ls if x<=8)/len(ls)))
# openings: first word
fw=collections.Counter(A.plain_text(p['body']).strip().split()[0] for p in news); print(fw.most_common(6))
# repeated trigrams across news
tri=collections.Counter()
for p in news:
    w=re.findall(r"[a-z']+",A.plain_text(p['body']).lower()); seen=set(zip(w,w[1:],w[2:],w[3:]))
    for g in seen: tri[g]+=1
stop={'the','a','of','to','in','and','is','it','that','for','on','was','with','as','at','by','this','be','are'}
print([(' '.join(g),n) for g,n in tri.most_common(400) if sum(1 for x in g if x in stop)<=1][:14])
# invented initial people in nonfiction (current text has labels; count posts with initials)
ini=[p['f'][:30] for p in posts if p['form'] not in ('fiction','five_years') and re.search(r"(?<![A-Za-z.])([B-HJ-WYZ])\.(?=[\s,'])",A.plain_text(p['body']))]
print('nonfiction posts with an initial-only person',len(ini))
# bets
b=json.load(open('agent/predictions.json')); st=collections.Counter(r['status'] for r in b); print('bets',len(b),st)
due=[r for r in b if r['due']<='2026-11-25']; print('due by today',len(due), collections.Counter(r['status'] for r in due))
yrs=collections.Counter(r['due'][:4] for r in b); print(yrs)
print('how-to count',c['how_to'],'days',len({p['date'] for p in posts}))
print('posts per day', round(len(posts)/len({p['date'] for p in posts}),1), 'total words', sum(A.visible_words(p['body']) for p in posts))
print('--- extra')
for m in ['2026-09','2026-10','2026-11']:
    ps=[p for p in news if p['date'].startswith(m)]
    print(m,len(ps),'formula',sum(1 for p in ps if A.check_title_formula(p['title'])),'Has',sum(1 for p in ps if re.search(r"\bHas\b",p['title'].rsplit("'",1)[-1])))
print('aug news',len([p for p in news if p['date'].startswith('2026-08')]))
print('The-start',sum(1 for p in news if A.plain_text(p['body']).strip().split()[0]=='The'))
print('news 2027/28 due', yrs['2027']+yrs['2028'])
print('says nothing about', sum(1 for p in posts if 'says nothing about' in p['body'].lower()), 'nobody', sum(1 for p in news if re.search(r'\bNobody\b',p['body'])), 'of', len(news))

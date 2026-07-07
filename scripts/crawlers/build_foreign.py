#!/usr/bin/env python3
# 外国公版声部: 按原名+国别判定语种 -> <lang>.wikisource.org 抓原文全作品 -> voices/<名>/corpus/text/
import urllib.parse, urllib.request, os, re, json, time, html as _html
from concurrent.futures import ThreadPoolExecutor

UA="voice-capsules-corpus/0.1 (research; yunyue.li@mirofish.ai)"
VOICES="/Users/admin/Desktop/Github/作家蒸馏/voices"
MD="/Users/admin/Desktop/Github/作家蒸馏/03-作家总名录.md"
_LIM=int(os.environ.get("LIMIT","0"))
ONLY=os.environ.get("ONLY","")   # 逗号分隔的"名"用于冒烟

# ---- 抽取外国目标 ----
region=None; foreign=[]
for ln in open(MD,encoding='utf-8'):
    s=ln.rstrip('\n'); m=re.match(r'^### (.+)',s)
    if m: region=m.group(1); continue
    if not s.startswith('|'): continue
    c=[x.strip() for x in s.strip('|').split('|')]
    if len(c)!=13 or c[0]=='名' or set(c[0])<=set('-: '): continue
    if region and region.startswith('中国'): continue
    foreign.append({"名":c[0],"原名":c[1],"时代":c[3],"版图":region,"代表作":[w for w in re.split(r'[、,，]',c[5]) if w.strip()]})
if ONLY: foreign=[t for t in foreign if t["名"] in ONLY.split(",")]
if _LIM: foreign=foreign[:_LIM]

def lang_of(t):
    s=t["原名"]
    if re.search(r'[Ѐ-ӿ]',s): return ['ru']
    if re.search(r'[぀-ヿ]',s): return ['ja']
    if re.search(r'[Ͱ-Ͽ]',s): return ['el']
    if re.search(r'[؀-ۿ]',s): return ['ar']
    if re.search(r'[֐-׿]',s): return ['he']
    tt=t["时代"]+t["版图"]
    for kw,lg in [('法国','fr'),('法语','fr'),('德','de'),('奥地利','de'),('奥匈','de'),('俄','ru'),('苏联','ru'),
                  ('意大利','it'),('西班牙','es'),('葡萄牙','pt'),('巴西','pt'),('波兰','pl'),('捷克','cs'),
                  ('挪威','no'),('瑞典','sv'),('丹麦','da'),('冰岛','is'),('芬兰','fi'),('荷兰','nl'),
                  ('日本','ja'),('希腊','el'),('阿拉伯','ar'),('希伯来','he'),('波斯','fa'),
                  ('英国','en'),('美国','en'),('爱尔兰','en'),('印度','en'),('尼日利亚','en'),('肯尼亚','en')]:
        if kw in tt: return [lg]
    if t["版图"].startswith('英语'): return ['en']
    if t["版图"].startswith('西语'): return ['es','pt']
    if t["版图"].startswith('日本'): return ['ja','en']
    if '欧陆' in t["版图"]: return ['fr','de','ru','it']
    return ['en']

CUT=['公有領域','公有领域','著作權','著作权','This work is in the public domain','This work was published',
     'is in the public domain','原作國家']
DROP=['◄','►','←','→','Wikisource','维基','維基','姊妹','sister projects','Sister Projects','出典',
      'This page was','edited by','[edit]']
def clean(raw):
    out=[]
    for l in (x.strip() for x in raw.splitlines()):
        if not l or '￼' in l: continue
        if any(k in l for k in CUT): break
        if any(k in l for k in DROP): continue
        out.append(l)
    return "\n".join(out)
def sane(s): return re.sub(r'[ /()（）《》\[\]|:*?"<>]','_',s).strip('_') or 'x'

def _get(url):
    for a in range(4):
        try: return urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":UA}),timeout=40).read()
        except urllib.error.HTTPError as e:
            if e.code in (429,503): time.sleep(3*(a+1)); continue
            if e.code==404: return None
            time.sleep(1.2*(a+1))
        except Exception: time.sleep(1.2*(a+1))
    return None
def api(lang,params):
    b=_get(f"https://{lang}.wikisource.org/w/api.php?"+urllib.parse.urlencode({**params,"format":"json","formatversion":"2"}))
    try: return json.loads(b) if b else None
    except Exception: return None
def search(lang,q,ns,limit=2):
    d=api(lang,{"action":"query","list":"search","srsearch":q,"srnamespace":str(ns),"srlimit":str(limit)})
    return [h["title"] for h in d.get("query",{}).get("search",[])] if d else []
def links_of(lang,title):
    d=api(lang,{"action":"parse","page":title,"prop":"links"})
    if not d or "parse" not in d: return None,[]
    return d["parse"]["title"],[l["title"] for l in d["parse"].get("links",[]) if l.get("ns")==0]
def fetch_text(lang,title):
    b=_get(f"https://{lang}.wikisource.org/api/rest_v1/page/html/"+urllib.parse.quote(title,safe=''))
    if not b: return None
    s=b.decode('utf-8','ignore')
    s=re.sub(r'(?is)<(script|style)\b.*?</\1>','',s)
    s=re.sub(r'(?i)</(p|div|li|h[1-6]|tr|blockquote|dd|dt)>','\n',s)
    s=re.sub(r'(?i)<(br|hr)\s*/?>','\n',s); s=re.sub(r'<[^>]+>','',s)
    try: return clean(_html.unescape(s))
    except Exception: return None
def save(voice,work,leaf,body):
    d=os.path.join(VOICES,sane(voice),"corpus","text",sane(work)); os.makedirs(d,exist_ok=True)
    open(os.path.join(d,sane(leaf)+".txt"),"w").write(body)

WORK_CAP=250; AWORKS_CAP=150
log=open(os.path.join(VOICES,"_build_foreign_log.txt"),"w")
def emit(m): print(m); log.write(m+"\n"); log.flush()

cov=[]
emit(f"外国目标 {len(foreign)}\n")
for i,t in enumerate(foreign,1):
    name=t["名"]; base=name.strip("《》")
    vdir=os.path.join(VOICES,sane(base),"corpus","text")
    if os.path.isdir(vdir) and any(os.scandir(vdir)): emit(f"[{i}/{len(foreign)}] 已存在跳过 {base}"); continue
    langs=lang_of(t); lang=None; ap=None
    for lg in langs:
        hit=search(lg,t["原名"] or base,102,1)
        if hit: lang=lg; ap=hit[0]; break
    if not ap:
        cov.append((base,"|".join(langs),t["原名"],"","无作者页",0,0,"未找到")); emit(f"[{i}/{len(foreign)}] {base:14} 语种{langs} 原名'{t['原名']}' -> 未找到作者页"); continue
    canon,alinks=links_of(lang,ap)
    works=[w for w in alinks if not re.match(r'^(Author|Auteur|Autor|Автор|著者|Portal|Wikisource|Help|Category|Portail|Portale):',w)][:AWORKS_CAP]
    if not works:                       # 作者页无作品链接(如莎士比亚挂Portal): 正文搜回退
        works=[h for h in search(lang,t["原名"] or base,0,40) if '/' not in h][:AWORKS_CAP]
    # 并发解析各作品子页
    def resolve(w):
        c2,sub=links_of(lang,w)
        if c2 is None: c2=w; sub=[]
        subp=[x for x in sub if x.startswith(c2+"/")][:WORK_CAP]
        return [(c2,p) for p in (subp if subp else [c2])]
    leaves=[]
    with ThreadPoolExecutor(max_workers=8) as ex:
        for r in ex.map(resolve, works): leaves+=r
    seen=set(); uniq=[cp for cp in leaves if not (cp[1] in seen or seen.add(cp[1]))]
    def dl(cp):
        c2,p=cp; b=fetch_text(lang,p)
        if not b or len(b)<40: return 0
        save(base,c2,p.split("/")[-1],b); return len(b)
    with ThreadPoolExecutor(max_workers=8) as ex:
        lens=list(ex.map(dl, uniq))
    tp=sum(1 for x in lens if x); tc=sum(lens)
    st="ok" if tp else "空"
    cov.append((base,lang,t["原名"],ap,f"works{len(works)}",tp,tc,st))
    emit(f"[{i}/{len(foreign)}] {base:14} [{lang}] {ap[:28]:28} 作品{len(works):3} 页{tp:4} 字{tc:>8} {st}")

with open(os.path.join(VOICES,"_coverage_foreign.tsv"),"w") as f:
    f.write("名\t语种\t原名\t作者页\t作品\t页数\t字数\t状态\n")
    for r in cov: f.write("\t".join(str(x) for x in r)+"\n")
emit(f"\n完成: {len([c for c in cov if c[7]=='ok'])} 有内容 / {len(cov)}; 总页 {sum(r[5] for r in cov)}; 总字 {sum(r[6] for r in cov)}")
log.close()

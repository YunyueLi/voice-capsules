#!/usr/bin/env python3
# 通用建库 v2: 名录中国公版声部 -> zh.wikisource 全作品 -> voices/<名>/corpus/text/
# 规则: 人名->搜作者页(ns102)+正史黑名单; 《作品》->正文搜(ns0)取顶层书名; 子页展开;
#       代表作兜底; 重试退避; 去重; 断点续跑; 每作者日志(错可见)
import urllib.parse, urllib.request, os, re, json, time, html as _html

UA="voice-capsules-corpus/0.1 (research; yunyue.li@mirofish.ai)"
API="https://zh.wikisource.org/w/api.php"
REST="https://zh.wikisource.org/api/rest_v1/page/html/"
VOICES="/Users/admin/Desktop/Github/作家蒸馏/voices"
SCR="/private/tmp/claude-501/-Users-admin-Desktop-Github-----/f3cfb99f-9da1-4794-8640-8a06ab71ee9b/scratchpad"
targets=json.load(open(os.path.join(SCR,"targets.json"),encoding="utf-8"))
_LIM=int(os.environ.get("LIMIT","0"))
if _LIM: targets=targets[:_LIM]

SKIP_PILOT=['鲁迅','老舍','曹雪芹','红楼梦']
# 正史/传记源(繁) -> 简, 用于「非本人史书则剔除」判定
HIST={'史記':'史记','漢書':'汉书','後漢書':'后汉书','三國志':'三国志','晉書':'晋书','宋書':'宋书',
'南齊書':'南齐书','梁書':'梁书','陳書':'陈书','魏書':'魏书','北齊書':'北齐书','周書':'周书','隋書':'隋书',
'南史':'南史','北史':'北史','舊唐書':'旧唐书','新唐書':'新唐书','舊五代史':'旧五代史','新五代史':'新五代史',
'宋史':'宋史','遼史':'辽史','金史':'金史','元史':'元史','明史':'明史','清史稿':'清史稿',
'資治通鑑':'资治通鉴','續資治通鑑':'续资治通鉴'}
# CUT: 尾部版权声明(遇到即截断其后全部); DROP: 页面装饰行(丢弃该行但继续)
CUT=['公有領域','公有领域','著作權','著作权','1996年1月1日','这部作品','這部作品','本作品現','根据《中华人民','原作國家']
DROP=['姊妹','維基文庫','维基文库','作者：','此版本取自','◄','►','←','→','Wikisource','出典',
      '维基百科','維基百科','文言維基','参阅','參閱','维基词典','維基詞典','维基大典','維基大典','维基语录','維基語錄']
WORK_CAP=250; AUTHORWORKS_CAP=150

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

def api(params):
    b=_get(API+"?"+urllib.parse.urlencode({**params,"format":"json","formatversion":"2"}))
    try: return json.loads(b) if b else None
    except Exception: return None

def search(q,ns,limit=3):
    d=api({"action":"query","list":"search","srsearch":q,"srnamespace":str(ns),"srlimit":str(limit)})
    return [h["title"] for h in d.get("query",{}).get("search",[])] if d else []

def links_of(title):
    d=api({"action":"parse","page":title,"prop":"links"})
    if not d or "parse" not in d: return None,[]
    return d["parse"]["title"],[l["title"] for l in d["parse"].get("links",[]) if l.get("ns")==0]

def clean(raw):
    out=[]
    for l in (x.strip() for x in raw.splitlines()):
        if not l or '￼' in l: continue
        if any(k in l for k in CUT): break
        if any(k in l for k in DROP): continue
        if re.fullmatch(r'\d{4}年\d{0,2}月?',l): continue
        out.append(l)
    return "\n".join(out)

def html2txt(b):
    s=b.decode('utf-8','ignore')
    s=re.sub(r'(?is)<(script|style)\b.*?</\1>','',s)
    s=re.sub(r'(?i)</(p|div|li|h[1-6]|tr|blockquote|dd|dt)>','\n',s)
    s=re.sub(r'(?i)<(br|hr)\s*/?>','\n',s)
    s=re.sub(r'<[^>]+>','',s)
    return _html.unescape(s)

def fetch_text(title):
    b=_get(REST+urllib.parse.quote(title,safe=''))
    if not b: return None
    try: return clean(html2txt(b))
    except Exception: return None

def save(voice,work,leaf,body):
    d=os.path.join(VOICES,sane(voice),"corpus","text",sane(work)); os.makedirs(d,exist_ok=True)
    open(os.path.join(d,sane(leaf)+".txt"),"w").write(body)

def grab_work(voice,work_title,seen):
    canon,alllinks=links_of(work_title)
    if canon is None: canon=work_title; alllinks=[]
    subs=[s for s in alllinks if s.startswith(canon+"/")][:WORK_CAP]
    pages=subs if subs else [canon]
    np=nc=0
    for p in pages:
        if p in seen: continue
        seen.add(p)
        b=fetch_text(p)
        if not b or len(b)<40: continue
        save(voice,canon,p.split("/")[-1],b); np+=1; nc+=len(b); time.sleep(0.05)
    return np,nc

log=open(os.path.join(VOICES,"_build_log.txt"),"w")
def emit(m): print(m); log.write(m+"\n"); log.flush()

cov=[]; done=set()
emit(f"目标 {len(targets)} 中国公版声部; 跳过试点 {SKIP_PILOT}\n")
for i,t in enumerate(targets,1):
    name=t["名"]; daibiao=t["代表作"]
    base=re.sub(r'[·・].*','',name.strip("《》")).strip()
    if any(p in name for p in SKIP_PILOT): emit(f"[{i}/{len(targets)}] 跳过(试点) {name}"); continue
    if base in done: emit(f"[{i}/{len(targets)}] 跳过(同作者已跑) {name}"); continue
    done.add(base)
    vdir=os.path.join(VOICES,sane(base),"corpus","text")
    if os.path.isdir(vdir) and any(os.scandir(vdir)): emit(f"[{i}/{len(targets)}] 已存在跳过 {base}"); continue
    seen=set(); works=[]; src=""
    dbtext="".join(daibiao)
    if name.startswith("《"):                      # 无名/作品声部: 正文搜顶层书名
        hits=search(base,0,6)
        NOISE=re.compile(r'判决|判決|裁定|纠纷|糾紛|民事|刑事|審|审判|公司|批评史|批評史|評傳|评传|二大罪|駁回|驳回|研究')
        top=[h for h in hits if "/" not in h and not NOISE.search(h)]
        if top: works=[top[0]]; src="work:"+top[0]
        else: works=[]; src="需人工|命中:"+("；".join(hits[:3]) if hits else "无")
    else:                                          # 人名: 作者页(ns102)
        ap=search(base,102,1)
        if ap:
            canon,alinks=links_of(ap[0])
            keep=[]
            for w in alinks:
                if w.startswith(("作者:","Author:")): continue
                b0=w.split("/")[0]
                if b0 in HIST and HIST[b0] not in dbtext: continue   # 非本人史书=传记源,剔
                keep.append(w)
            works=keep[:AUTHORWORKS_CAP]; src=f"{ap[0]}({len(works)})"
        if not works: works=list(dict.fromkeys(daibiao)); src=(src or "")+"代表作兜底"
    tp=tc=0
    for w in works:
        try: a,b=grab_work(base,w,seen); tp+=a; tc+=b
        except Exception as e: emit(f"    ! {base}/{w}: {str(e)[:50]}")
    st="ok" if tp else "空"
    cov.append((base,t["版图"],t["级"],src[:40],len(works),tp,tc,st))
    emit(f"[{i}/{len(targets)}] {base:10} | {src[:34]:34} | 作品{len(works):3} 页{tp:4} 字{tc:>8} {st}")

with open(os.path.join(VOICES,"_coverage.tsv"),"w") as f:
    f.write("作者\t版图\t级\t来源\t作品数\t页数\t字数\t状态\n")
    for r in cov: f.write("\t".join(str(x) for x in r)+"\n")
emit(f"\n完成: {len([c for c in cov if c[7]=='ok'])} 声部有内容 / {len(cov)} 尝试; 总页 {sum(r[5] for r in cov)}; 总字 {sum(r[6] for r in cov)}")
log.close()

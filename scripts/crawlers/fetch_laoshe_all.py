#!/usr/bin/env python3
# 老舍·小说 全量抓取(长篇11 + 短篇集8),按 作者:老舍 目录; 排除话剧/散文/回译
import urllib.parse, urllib.request, subprocess, os, re, tempfile, json, time, shutil

UA="voice-capsules-corpus/0.1 (research; yunyue.li@mirofish.ai)"
API="https://zh.wikisource.org/w/api.php"
REST="https://zh.wikisource.org/api/rest_v1/page/html/"
BASE="/Users/admin/Desktop/Github/作家蒸馏/voices/lao-she-fiction/corpus/text"
if os.path.exists(BASE): shutil.rmtree(BASE)   # 重建,清晰整理
os.makedirs(BASE, exist_ok=True)

PD=['公有領域','公有领域','著作權','著作权','本作品','这部作品','這部作品','1996年1月1日','姊妹計','姊妹计']
NAV=['作者：','此版本取自','←','→']

CHANGPIAN=['老張的哲學','趙子曰','二馬','貓城記','離婚 (老舍)','牛天賜傳','文博士',
           '駱駝祥子','火葬','我這一輩子','四世同堂']   # 鼓書藝人=回译排除; 正紅旗下 试探
DUANPIAN=['赶集','樱海集','蛤藻集','火车集','贫血集','集外','微神集','月牙集']
TRY_EXTRA=['正紅旗下']

def api(params):
    params={**params,"format":"json","formatversion":"2"}
    req=urllib.request.Request(API+"?"+urllib.parse.urlencode(params),headers={"User-Agent":UA})
    return json.load(urllib.request.urlopen(req,timeout=30))

def subpages(work):
    try: d=api({"action":"parse","page":work,"prop":"links"})
    except Exception: return None,[]
    if "parse" not in d: return None,[]
    canon=d["parse"]["title"]
    subs=[l["title"] for l in d["parse"].get("links",[]) if l.get("ns")==0 and l["title"].startswith(canon+"/")]
    return canon,subs

def clean(raw):
    out=[]
    for l in (x.strip() for x in raw.splitlines()):
        if not l or '￼' in l: continue
        if any(k in l for k in PD): break
        if any(k in l for k in NAV): continue
        if re.fullmatch(r'\d{4}年\d{0,2}月?',l): continue
        if re.fullmatch(r'《.*》和.*',l): continue
        out.append(l)
    return "\n".join(out)

def fetch(title):
    url=REST+urllib.parse.quote(title,safe='')
    try: html=urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":UA}),timeout=30).read()
    except Exception as e: return None
    h=tempfile.NamedTemporaryFile(suffix=".html",delete=False);h.write(html);h.close()
    tp=h.name+".txt";subprocess.run(["textutil","-convert","txt","-encoding","UTF-8",h.name,"-output",tp],capture_output=True)
    try: body=clean(open(tp,encoding="utf-8").read())
    except Exception: body=None
    os.unlink(h.name); os.path.exists(tp) and os.unlink(tp)
    return body

def do(work, cat):
    canon,subs=subpages(work)
    if canon is None:
        print(f"  ✗ {work} 页面不存在"); return 0,0
    wdir=os.path.join(BASE,cat,re.sub(r'[ /()（）]','_',canon))
    pages= subs if subs else [canon]
    os.makedirs(wdir,exist_ok=True)
    tot=0;ok=0
    for p in pages:
        body=fetch(p)
        if not body or len(body)<40: continue
        fn=re.sub(r'[ /()（）]','_',p.split('/')[-1])
        open(os.path.join(wdir,fn+".txt"),"w").write(body);tot+=len(body);ok+=1;time.sleep(0.1)
    print(f"  ✓ {canon:12} [{cat}] {ok} 节 {tot} 字" + ("" if subs else " (单页)"))
    return ok,tot

print("=== 长篇小说 ===")
gt=gc=0
for w in CHANGPIAN+TRY_EXTRA:
    o,c=do(w,"长篇小说"); gt+=o; gc+=c
print("=== 短篇小说集 ===")
for w in DUANPIAN:
    o,c=do(w,"短篇小说集"); gt+=o; gc+=c
print(f"\n老舍·小说 合计 {gt} 个文本文件, {gc} 字")

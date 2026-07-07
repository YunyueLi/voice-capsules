#!/usr/bin/env python3
# 青空文庫: 按作品著作权标志(なし=公版)筛选 + 匹配名录日本作者 -> 拉正文入库
import csv, os, re, urllib.request, time, html as _html
UA="voice-capsules-corpus/0.1 (research; yunyue.li@mirofish.ai)"
CSV="/private/tmp/claude-501/-Users-admin-Desktop-Github-----/f3cfb99f-9da1-4794-8640-8a06ab71ee9b/scratchpad/aozora_csv/list_person_all_extended_utf8.csv"
VOICES="/Users/admin/Desktop/Github/作家蒸馏/voices"

def norm(s): return s.replace('鷗','鸥').replace('鴎','鸥').replace('龍','龙').replace('竜','龙').replace('槇','槙').replace(' ','').replace('　','')
# 名录日本作者: 原名(Aozora风格) -> 声部名(建库目录)
ROSTER={'紫式部':'紫式部','清少納言':'清少纳言','吉田兼好':'吉田兼好','松尾芭蕉':'松尾芭蕉','小林一茶':'小林一茶',
'井原西鶴':'井原西鹤','夏目漱石':'夏目漱石','森鴎外':'森鸥外','森鷗外':'森鸥外','樋口一葉':'樋口一叶',
'芥川龍之介':'芥川龙之介','谷崎潤一郎':'谷崎润一郎','太宰治':'太宰治','江戸川乱歩':'江户川乱步','星新一':'星新一'}
ROSTER={norm(k):v for k,v in ROSTER.items()}

def _get(url):
    for a in range(4):
        try: return urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":UA}),timeout=40).read()
        except urllib.error.HTTPError as e:
            if e.code in(429,503): time.sleep(3*(a+1)); continue
            if e.code==404: return None
            time.sleep(1.2*(a+1))
        except Exception: time.sleep(1.2*(a+1))
    return None
def sane(s): return re.sub(r'[ /()（）《》\[\]|:*?"<>　]','_',s).strip('_') or 'x'

def clean_html(b,charset):
    enc='utf-8' if charset and 'utf' in charset.lower() else 'shift_jis'
    s=b.decode(enc,'ignore')
    m=re.search(r'(?is)<div class="main_text">(.*?)</div>\s*(?:<div|<hr|$)',s)
    body=m.group(1) if m else s
    body=re.sub(r'(?is)<rp>.*?</rp>','',body)
    body=re.sub(r'(?is)<rt>.*?</rt>','',body)
    body=re.sub(r'(?i)<br\s*/?>','\n',body)
    body=re.sub(r'(?is)<[^>]+>','',body)
    body=_html.unescape(body)
    body=re.sub(r'《[^》]*》','',body)
    body=re.sub(r'［＃[^］]*］','',body)
    body=body.replace('｜','')
    return "\n".join(l.strip() for l in body.splitlines() if l.strip())

# 收集目标作品
jobs={}  # voice -> [(title,url,charset)]
with open(CSV,encoding='utf-8') as f:
    r=csv.reader(f); next(r)
    for row in r:
        if len(row)<52: continue
        if row[10]!='なし': continue          # 只要公版作品
        name=norm(row[15]+row[16])
        if name not in ROSTER: continue
        url=row[50] or row[45]                # XHTML优先
        if not url or not url.startswith('http'): continue
        charset=row[53] if len(row)>53 else ''
        jobs.setdefault(ROSTER[name],[]).append((row[1],url,charset))

log=open(os.path.join(VOICES,"_build_aozora_log.txt"),"w")
def emit(m): print(m); log.write(m+"\n"); log.flush()
emit(f"青空文庫: 匹配到 {len(jobs)} 位作者, 公版作品共 {sum(len(v) for v in jobs.values())} 篇\n")
cov=[]
for voice,items in jobs.items():
    d=os.path.join(VOICES,sane(voice),"corpus","text","aozora"); os.makedirs(d,exist_ok=True)
    tp=tc=0
    for title,url,cs in items:
        if not url.endswith(('.html','.htm')): continue   # 只走HTML版
        b=_get(url)
        if not b: continue
        try: body=clean_html(b,cs)
        except Exception: continue
        if len(body)<40: continue
        open(os.path.join(d,sane(title)+".txt"),"w").write(body); tp+=1; tc+=len(body); time.sleep(0.05)
    cov.append((voice,len(items),tp,tc))
    emit(f"{voice:10} 篇目{len(items):4} 存{tp:4} 字{tc:>9}")
with open(os.path.join(VOICES,"_coverage_aozora.tsv"),"w") as f:
    f.write("作者\t公版篇数\t已存\t字数\n")
    for r in cov: f.write("\t".join(str(x) for x in r)+"\n")
emit(f"\n完成: {sum(r[2] for r in cov)} 篇入库, {sum(r[3] for r in cov)} 字")
log.close()

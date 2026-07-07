#!/usr/bin/env python3
import urllib.parse, urllib.request, subprocess, os, re, time, tempfile

UA = "voice-capsules-corpus/0.1 (research; yunyue.li@mirofish.ai)"
REST = "https://zh.wikisource.org/api/rest_v1/page/html/"
ROOT = "/Users/admin/Desktop/Github/作家蒸馏/voices"

PD = ['公有領域','公有领域','著作權','著作权','本作品','这部作品','這部作品',
      '1996年1月1日','版權期限','姊妹計','姊妹计']
NAV = ['作者：','此版本取自','←','→']

def fetch_txt(title):
    url = REST + urllib.parse.quote(title, safe='')
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        html = urllib.request.urlopen(req, timeout=30).read()
    except Exception as e:
        return None, f"ERR {e}"
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
        f.write(html); hp = f.name
    tp = hp + ".txt"
    subprocess.run(["textutil","-convert","txt","-encoding","UTF-8",hp,"-output",tp],
                   capture_output=True)
    try:
        raw = open(tp, encoding="utf-8").read()
    except Exception as e:
        return None, f"txt-ERR {e}"
    os.unlink(hp);
    if os.path.exists(tp): os.unlink(tp)
    # 清洗
    lines = [l.strip() for l in raw.splitlines()]
    out, cut = [], False
    for l in lines:
        if not l: continue
        if '￼' in l: continue
        if any(k in l for k in PD): cut = True; break
        if any(l.startswith(k) or k in l for k in NAV): continue
        if re.fullmatch(r'\d{4}年\d{0,2}月?', l): continue
        if re.fullmatch(r'《.*》和.*', l): continue
        out.append(l)
    body = "\n".join(out)
    return body, "ok"

def save(voice, sub, name, body):
    d = os.path.join(ROOT, voice, "corpus", "text", sub)
    os.makedirs(d, exist_ok=True)
    safe = re.sub(r'[ /()（）]', '_', name)
    open(os.path.join(d, safe + ".txt"), "w").write(body)

jobs = []  # (voice, sub, name, title)
# 鲁迅
for t in ['狂人日記','孔乙己','藥','明天','一件小事','頭髮的故事','風波','故鄉','阿Ｑ正傳','端午節','白光','兔和貓','鴨的喜劇','社戲']:
    jobs.append(('lu-xun-fiction','nahan',t,t))
for t in ['祝福','弟兄','離婚','幸福的家庭','傷逝 (魯迅)','長明燈','孤獨者','高老夫子','示衆','肥皂','在酒樓上']:
    jobs.append(('lu-xun-fiction','panghuang',t,t))
for t in ['補天','奔月','理水','采薇 (鲁迅)','鑄劍','出關','非攻','起死']:
    jobs.append(('lu-xun-fiction','gushixinbian',t,t))
# 老舍单页
for t in ['月牙兒','斷魂槍']:
    jobs.append(('lao-she-fiction','duanpian',t,t))
# 老舍长篇(子页)
for work,n in [('駱駝祥子',24),('牛天赐传',24),('四世同堂',87),('我这一辈子',16)]:
    for i in range(1,n+1):
        jobs.append(('lao-she-fiction',work,f'{work}_{i:02d}',f'{work}/{i}'))

fail=[]; tot={}
for voice,sub,name,title in jobs:
    body,st = fetch_txt(title)
    if body is None or len(body)<50:
        fail.append((name,st,len(body) if body else 0));
        time.sleep(0.1); continue
    save(voice,sub,name,body)
    tot[sub]=tot.get(sub,0)+len(body)
    time.sleep(0.12)

print("=== 每部字数汇总 ===")
for k,v in tot.items(): print(f"{k:14} {v}")
print(f"\n成功 {len(jobs)-len(fail)}/{len(jobs)}")
if fail:
    print("失败/过短:")
    for f in fail: print("  ",f)

#!/usr/bin/env python3
# 抓取维基文库《脂硯齋重評石頭記》(脂本汇校本) 前80回
# 存: raw wikitext(含批语,凭证) + cleaned 正文(剥批语/模板/ref)
import json, re, time, urllib.parse, urllib.request, os, sys

UA = "voice-capsules-corpus/0.1 (research; yunyue.li@mirofish.ai)"
API = "https://zh.wikisource.org/w/api.php"
BASE = "/Users/admin/Desktop/Github/作家蒸馏/voices/hongloumeng/corpus"
RAW = os.path.join(BASE, "raw"); TXT = os.path.join(BASE, "text")
os.makedirs(RAW, exist_ok=True); os.makedirs(TXT, exist_ok=True)

def api_get(params):
    params = {**params, "format": "json", "formatversion": "2"}
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

# 1. allpages 拿子页清单
titles = []
apcontinue = None
while True:
    p = {"action": "query", "list": "allpages", "apprefix": "脂硯齋重評石頭記/",
         "apnamespace": "0", "aplimit": "500"}
    if apcontinue: p["apcontinue"] = apcontinue
    d = api_get(p)
    titles += [x["title"] for x in d["query"]["allpages"]]
    if "continue" in d: apcontinue = d["continue"]["apcontinue"]
    else: break
    time.sleep(0.2)

# 只要 "第N回" 章节页
chap = [t for t in titles if re.search(r"/第.+回$", t)]
other = [t for t in titles if t not in chap]
print(f"allpages 共 {len(titles)} 页; 章节页 {len(chap)}; 其他: {other}")

def clean(wt):
    n_piping = len(re.findall(r"\{\{~+\|", wt))  # 批语条数(近似)
    # 抽回目
    m = re.search(r"\|\s*section\s*=\s*(.+)", wt)
    huimu = ""
    if m:
        huimu = re.sub(r"'''", "", m.group(1)).strip()
        huimu = re.sub(r"\[\[[^\]]*\]\]", "", huimu).strip()
    t = wt
    t = re.sub(r"<ref[^>]*>.*?</ref>", "", t, flags=re.S)  # 注音注释
    t = re.sub(r"<ref[^>]*/>", "", t)
    t = re.sub(r"-\{[^{}]*\}-", "", t)                      # 繁简转换指令
    # 反复剥最内层 {{...}} —— header/批语/Pd 模板全清
    prev = None
    while prev != t:
        prev = t
        t = re.sub(r"\{\{[^{}]*\}\}", "", t)
    t = re.sub(r"\[\[[^\]|]*\|([^\]]*)\]\]", r"\1", t)      # [[a|b]]->b
    t = re.sub(r"\[\[([^\]]*)\]\]", r"\1", t)               # [[a]]->a
    t = re.sub(r"<[^>]+>", "", t)                            # 残余标签
    t = re.sub(r"''+", "", t)
    lines = [ln.strip() for ln in t.splitlines()]
    lines = [ln for ln in lines if ln]
    body = "\n".join(lines)
    if huimu:
        body = huimu + "\n" + body
    return body, n_piping, huimu

summary = []
for t in sorted(chap, key=lambda s: len(s)) if False else chap:
    d = api_get({"action": "query", "titles": t, "prop": "revisions",
                 "rvprop": "content", "rvslots": "main"})
    pg = d["query"]["pages"][0]
    if "revisions" not in pg:
        print("!! 无内容:", t); continue
    wt = pg["revisions"][0]["slots"]["main"]["content"]
    safe = t.split("/")[-1]  # 第N回
    open(os.path.join(RAW, safe + ".wikitext"), "w").write(wt)
    body, npi, huimu = clean(wt)
    open(os.path.join(TXT, safe + ".txt"), "w").write(body)
    summary.append((safe, len(wt), len(body), npi, huimu[:24]))
    time.sleep(0.25)

print("\n回目 | rawchars | cleanchars | 批语数 | 回目摘要")
for s in summary:
    print(f"{s[0]:>6} | {s[1]:>7} | {s[2]:>7} | {s[3]:>4} | {s[4]}")
print(f"\n共 {len(summary)} 回; 正文总字数 {sum(s[2] for s in summary)}")

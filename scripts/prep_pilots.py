#!/usr/bin/env python3
"""V0 第0步:三试点语料 清洗 + 繁简统一(t2s) + 冻结切分 + 底本说明。

输入:  原文/<作者>/...
输出:  声部/<声部>/语料/{train,test}/*.txt   (清洗+规范化后的正文，gitignore)
        语料索引/试点/<声部>-底本说明.md          (corpus-lock，入仓)
        语料索引/试点/<声部>-考卷清单.tsv          (held-out 文件名+哈希+字数，入仓，冻结)

纪律:
- 考卷(test)一旦生成即冻结:后续写风格分析的 agent 只能读 train，物理不碰 test。
- 切分以「篇/回/部」为单位(不按字符切)，防同篇跨集泄漏。
- 随机切分用固定种子(42)，可复现。
"""
import os, re, json, hashlib, random

ROOT = "/Users/admin/Desktop/Github/作家蒸馏"
SRC  = os.path.join(ROOT, "原文")
CAP  = os.path.join(ROOT, "声部")
IDX  = os.path.join(ROOT, "语料索引", "试点")
SEED = 42
TEST_RATIO = 0.30

import opencc
t2s = opencc.OpenCC("t2s")

def sha16(s): return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]
def nchars(s): return len(re.sub(r"\s", "", s))

# ---------- 清洗器 ----------
# 只用「句子级」标点判定正文；书名号/引号不算——否则开头的集名「《彷徨》」会被误当正文。
BODY_PUNC = "，。！？；：、"
# 维基编者注(交叉引用/出处/维基条目),即便带句号也要剥；只在开头短行生效，不碰正文。
# 注:清洗前已转简，这里只需匹配简体。
EDNOTE = re.compile(r"(参见.*版本|见.*版本|最初发表|发表于|选自|节选自|据.{0,8}版本|维基百科|维基文库|条目[:：]|本文初刊|初刊于)")
# 强编者注前缀:正文绝不会这样开头，故不限长度(仅在开头区生效)。
EDPREFIX = re.compile(r"^(本文初刊|本篇?最初发表|最初发表|本文发表|本篇发表|另参见|据[^，。]{0,12}版本)")

def clean_luxun(text):
    """剥离每篇开头混入的维基导航块(上一篇/本篇/下一篇标题、日期行、集名《呐喊》/《彷徨》、编者注)。
    规则:从头丢弃「短且无句子级标点」或「编者注」的行，直到第一行正文。"""
    lines = text.split("\n")
    i, stripped = 0, []
    while i < len(lines) and i < 10:           # 安全上限:最多丢 10 行
        ln = lines[i].strip()
        if ln == "" or (len(ln) <= 30 and not any(p in ln for p in BODY_PUNC)) or (len(ln) < 45 and EDNOTE.search(ln)) or EDPREFIX.match(ln):
            if ln: stripped.append(ln)
            i += 1
        else:
            break
    body = "\n".join(lines[i:]).strip()
    return body, stripped

def clean_hlm(text):
    """删除行尾孤立的 ==注释==/==注釋== 空 stub；保留回目标题行。"""
    text = re.sub(r"\n*==\s*注[释釋]\s*==\s*$", "", text.strip())
    return text.strip(), []

DOYLE_DROP = re.compile(
    r"(project\s+gutenberg|proofreading|distributed proofread|www\.pgdp\.net|"
    r"copyright,|george h\. doran|charles scribner|produced by|"
    r"transcrib|\*\*\*\s*start of|\*\*\*\s*end of|ebook|etext)", re.I)
def clean_doyle(text):
    """剥离残留的 Gutenberg 页眉/页脚行。"""
    kept, stripped = [], []
    for ln in text.split("\n"):
        if DOYLE_DROP.search(ln): stripped.append(ln.strip())
        else: kept.append(ln)
    return "\n".join(kept).strip(), stripped

# ---------- 试点定义 ----------
def luxun_files():
    out = []
    for sub in ("呐喊", "彷徨"):                # 故事新编另立声部(戏仿改写，腔调不同)，V0 排除
        d = os.path.join(SRC, "鲁迅", sub)
        for fn in sorted(os.listdir(d)):
            if fn.endswith(".txt"):
                name = re.sub(r"_+(鲁迅|魯迅)_*", "", fn[:-4]).strip("_")  # 去文件名残留
                out.append((f"{sub}·{name}", os.path.join(d, fn)))
    return out

def hlm_files():
    d = os.path.join(SRC, "红楼梦")
    fs = [fn for fn in os.listdir(d) if fn.endswith(".txt")]
    def num(fn):
        m = re.search(r"第(.+?)回", fn);
        return fn
    return [(fn[:-4], os.path.join(d, fn)) for fn in sorted(fs)]

DOYLE_CANON = [
    ("血字的研究",      "244_A_Study_in_Scarlet.txt"),
    ("四签名",          "2097_The_Sign_of_the_Four.txt"),
    ("福尔摩斯冒险史",  "1661_The_Adventures_of_Sherlock_Holmes.txt"),
    ("福尔摩斯回忆录",  "834_The_Memoirs_of_Sherlock_Holmes.txt"),
    ("巴斯克维尔的猎犬","2852_The_Hound_of_the_Baskervilles.txt"),
    ("福尔摩斯归来",    "108_The_Return_of_Sherlock_Holmes.txt"),
    ("恐怖谷",          "3289_The_Valley_of_Fear.txt"),
    ("最后致意",        "2350_His_last_bow.txt"),
    ("新探案",          "The_Case-Book_of_Sherlock_Holmes/The_Case-Book_of_Sherlock_Holmes.txt"),
]
def doyle_files():
    d = os.path.join(SRC, "柯南·道尔")
    out = []
    for name, rel in DOYLE_CANON:
        p = os.path.join(d, rel)
        if os.path.exists(p): out.append((name, p))
        else: print(f"  ⚠ 道尔缺失: {rel}")
    return out

PILOTS = {
    "鲁迅·小说":          dict(files=luxun_files, clean=clean_luxun, convert=True,
                              底本="呐喊(1923)+彷徨(1926) 全 25 篇；故事新编另立声部，排除。繁体经 OpenCC t2s 转简。"),
    "红楼梦":             dict(files=hlm_files,   clean=clean_hlm,   convert=True,
                              底本="庚辰脂本系前 80 回正文(已去脂批)。脂批不入语言层指纹(评点者之言)。繁体转简。后40回程高续书=负样本，待补。"),
    "柯南·道尔·福尔摩斯": dict(files=doyle_files, clean=clean_doyle, convert=False,
                              底本="福尔摩斯正传九部(1887–1927)，每部取一个干净 Gutenberg 副本、已去重去页脚。英文原文，不转换。"),
}

# ---------- 主流程 ----------
os.makedirs(IDX, exist_ok=True)
rng = random.Random(SEED)
summary = []
for voice, cfg in PILOTS.items():
    files = cfg["files"]()
    cleaned = []
    strip_log = []
    for name, path in files:
        raw = open(path, encoding="utf-8", errors="ignore").read()
        if cfg["convert"]: raw = t2s.convert(raw)     # 先转简，再清洗(清洗规则按简体写)
        body, stripped = cfg["clean"](raw)
        if nchars(body) < 100:                 # 空/坏文件跳过
            print(f"  ⚠ {voice} 跳过近空文件: {name} ({nchars(body)}字)"); continue
        cleaned.append((name, body))
        if stripped: strip_log.append((name, stripped))
    # 冻结切分:按篇/回/部为单位
    idxs = list(range(len(cleaned))); rng.shuffle(idxs)
    ntest = max(1, round(len(idxs) * TEST_RATIO))
    test_set = set(idxs[:ntest])
    vdir = os.path.join(CAP, voice)
    tr_dir, te_dir = os.path.join(vdir, "语料", "train"), os.path.join(vdir, "语料", "test")
    os.makedirs(tr_dir, exist_ok=True); os.makedirs(te_dir, exist_ok=True)
    manifest = []
    tr_c = te_c = 0
    def safe(n): return re.sub(r"[/\\]", "_", n)
    for k, (name, body) in enumerate(cleaned):
        split = "test" if k in test_set else "train"
        fp = os.path.join(te_dir if split == "test" else tr_dir, safe(name) + ".txt")
        open(fp, "w", encoding="utf-8").write(body)
        c = nchars(body)
        if split == "test":
            te_c += c; manifest.append((name, c, sha16(body)))
        else:
            tr_c += c
    # 考卷清单(入仓，冻结)
    with open(os.path.join(IDX, f"{voice}-考卷清单.tsv"), "w", encoding="utf-8") as f:
        f.write("# 冻结考卷(held-out)。写风格分析时禁止读取。种子=42\n篇目\t字数\tsha256_16\n")
        for name, c, h in sorted(manifest): f.write(f"{name}\t{c}\t{h}\n")
    # 底本说明(入仓)
    with open(os.path.join(IDX, f"{voice}-底本说明.md"), "w", encoding="utf-8") as f:
        f.write(f"# {voice} · 底本说明 (corpus-lock)\n\n")
        f.write(f"- **底本**：{cfg['底本']}\n")
        f.write(f"- **清洗**：{cfg['clean'].__name__}；共 {len(cleaned)} 个单位\n")
        f.write(f"- **繁简**：{'OpenCC t2s 转简体' if cfg['convert'] else '英文原文，不转换'}\n")
        f.write(f"- **切分**：按篇/回/部为单位，种子 42，考卷比例 {TEST_RATIO:.0%}\n")
        f.write(f"  - 训练集 {len(cleaned)-ntest} 单位 / {tr_c:,} 字\n")
        f.write(f"  - 考卷集 {ntest} 单位 / {te_c:,} 字（清单见同目录 `{voice}-考卷清单.tsv`）\n")
        if strip_log:
            f.write(f"- **剥离记录**（清洗剥掉的非正文行，抽样）：\n")
            for name, st in strip_log[:5]:
                f.write(f"  - {name}: {st}\n")
    summary.append((voice, len(cleaned), len(cleaned)-ntest, ntest, tr_c, te_c, len(strip_log)))

print("\n=== 第0步完成 ===")
print(f"{'声部':<22}{'单位':>5}{'训练':>5}{'考卷':>5}{'训练字数':>12}{'考卷字数':>12}{'剥离篇数':>8}")
for v, n, tr, te, trc, tec, sl in summary:
    print(f"{v:<22}{n:>5}{tr:>5}{te:>5}{trc:>12,}{tec:>12,}{sl:>8}")

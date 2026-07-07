# scripts/ · 语料工程脚本

## prep_pilots.py（当前，可运行）
V0 第0步:三试点语料 清洗 + 繁简统一(t2s) + 冻结切分 + 底本说明。
- 输入 `原文/`，输出 `声部/<声部>/语料/{train,test}/`（gitignore）+ `语料索引/试点/`（入仓元数据）。
- 运行:`./.venv/bin/python scripts/prep_pilots.py`（依赖见根目录 `requirements.txt`）。
- 切分种子固定 42、按篇/回/部为单位，考卷(held-out)一旦提交即冻结。

## crawlers/ · 建库脚本（存档，非即开即用）
四条公版语料管线 + 三个试点抓取脚本 + 结构重排，**从会话临时目录抢救入仓**（此前散在 scratchpad，随时会丢，属"语料不可复现"的 P0）。
- `build_library.py` — 中文公版(zh.wikisource)
- `build_aozora.py` — 日本公版(青空文库，按著作权 flag)
- `build_foreign.py` — 外国各语种(wikisource，多线程)
- `build_gutenberg.py` — 英语公版(Project Gutenberg)
- `fetch_hlm.py / fetch_lu_lao.py / fetch_laoshe_all.py` — 三试点精抓
- `reorg.py` — `voices/` → `原文/` 结构规范化（已执行过）

**已知问题（重跑前必读）：**
1. **路径硬编码**到旧 scratchpad 绝对路径，重跑需改 `SRC/OUT` 常量。
2. **`build_library.py` 的模糊匹配有 bug**：把部分版权期内、zh.wikisource 无源的作者，错配到了同名/近名的公版古人，抓成了**错的人**的文本。已确认的错配：王小波→王士禛(清)、木心/曹禺→黎遂球(明)、汪曾祺→蔡和森、杨牧→杜牧。这些 `原文/<作者>/` 目录里装的是那位古人的公版文本（**非盗版，但张冠李戴**）。重建每作者语料或覆盖索引前，必须先做作者名消歧、剔除错配目录。修法：解析器命中不确定时应返回"未找到"，而不是强行取同页链接里的近名人物。
3. **无 per-file 来源清单**：目前未记录每篇的源 URL/抓取日期/哈希。合法性台账(04 §7 要求)尚缺，待补 `语料索引/来源台账`。

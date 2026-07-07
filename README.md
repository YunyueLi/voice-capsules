# 作家蒸馏（Voice Capsules）

一句话：为古今中外最璀璨的文学巨匠各建一个独立的「作家封装」，把一位作家的遣词、叙事、结构、人物、世界观乃至「他绝不做什么」，完整蒸馏成可调用、可评测、可复用的能力包。

> **English**: Voice Capsules is an open methodology for distilling the great writers of world literature into callable, *evaluable* capability packages. Each "voice" (an author may have several) is reverse-engineered across seven layers — diction, narration, structure, character, worldview, reader contract, and knowledge/persona substrate — plus its **negative space** (what the author never does, the single biggest tell in AI pastiche). The core asset is not a generation prompt but a per-voice **discriminator** ("does this read like Lu Xun?" is a measurable question), which drives a generate → judge → attribute-the-gap → iterate bootstrap loop. Docs are currently in Chinese; the roster covers 424 candidate voices across Chinese classical/modern, English, continental European, Hispanic, Japanese and other literatures.

**项目状态**：方法论文档 + 本地公版语料库；V0 判别器地基建设中（2026-07 开工前对抗审查后补地基）。欢迎 issue 讨论名录、七层模型与判别器设计。License: [MIT](LICENSE)。

## 文档地图

| 文档 | 内容 | 状态 |
|---|---|---|
| [01-愿景与需求](01-愿景与需求.md) | 想法的完整整理：蒸馏对象的七层拆解、声部单位、翻译问题、与大模型厂商的本质区别、L1/L2/L3 承诺分层 | 初稿 |
| [02-作家封装架构](02-作家封装架构.md) | Voice Capsule 规范：封装目录、各层内容纪律、蒸馏流水线、三层判别器、技术路线取舍、试点声部 | 初稿 |
| [03-作家总名录](03-作家总名录.md) | 全球版图长表（424 候选声部）+ P0/P1/P2 分级 + 第一批约 40 声部建议 + 译者声部 | v1 |
| [04-研究与竞品调研](04-研究与竞品调研.md) | 学术、开源、产品、法律全景调研，带来源链接 + 对方案的修订清单 | v1 |
| [05-对抗性审查](05-对抗性审查.md) | 5 路 55 个攻击点的判定与处置、v1.1 返工清单、留给决策者的三个开放问题 | v1 |

## 核心概念速览

- **声部（Voice）**：封装的基本单位。一个作家可拆多个声部（鲁迅·小说 / 鲁迅·杂文），一部无名氏经典自成声部（《水浒传》）。
- **七层模型**：语言 → 叙事 → 结构 → 人物 → 世界观 → 读者契约 → 知识与人格底座；外加负空间（露馅清单）与演化轴两条贯穿轴。
- **判别器是核心资产**：判的是「**新生成/未见文本**像不像该作家」——不是「查这段真迹是谁写的」（后者搜索/RAG 即得、无需本项目）。它是服务于写作（生成/改写/点评）的**评测尺子 + 拒绝采样筛子**，不是文本溯源工具。计量指纹 + LLM rubric + 人类盲测三层判别，既做验收，也把输出推向分布尾部。
- **承诺分层**：L1 文体指纹保真（可达）/ L2 写作方法论复用（价值假说，验收=决策规则命中率）/ L3 原创灵光（不承诺——严判别器在机制上会杀掉「恰当背叛惯例」的候选，L3 专用通道是未验证的开放问题）。

## 当前状态

- 2026-07-03：立项日完成一个完整循环——需求与架构初稿 → 15 路调研与盘点（424 候选声部）→ 5 路对抗性审查（55 个攻击点，15 个 P0）→ 全部必改项回填。
- 试点定为：鲁迅·小说、《红楼梦》、老舍·小说。V0 第一交付物 = 中文判别精度基线报告 + spec vs naive prompt 消融数据。判决线见 01 第九节。
- 2026-07-05 拍板（详见 05 第五节）：商业形态走**纯研究/开源**（译者声部产品挂条件、遗产授权推迟）；判决线锁为**规则**（数值等基线报告按公式算）；盲测网络 **V0 暂不建**，人类盲测推迟到消融数据出来后作为发布门。

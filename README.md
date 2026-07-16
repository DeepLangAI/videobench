# VideoBench

一个直接评估视频的 benchmark：**输入是产出的成片（可附任务参照），输出是判定**。只评视频本身，不评生成系统——成功率、耗时、成本、稳定性是生成链路的监控指标，不在本 benchmark 范围内。

评估不是为了排行榜，而是为了闭环里的"评估→定位问题"这一环：

```
生成 → [VideoBench: 评估 → 定位问题] → 优化系统 → 再生成
```

## 质量的定义

质量 ≠ 画面生成质量。一条成片"好"，意味着同时满足：任务完成、信息传达正确、有观看价值、符合品牌和平台约束、可直接进入真实生产流程。

## 三级判定

完整评估 = 合格性检测 + 多维诊断 + GSB 决策，而不是只跑一次 GSB。

| 层级 | 回答的问题 | 方法 | 文档 |
|---|---|---|---|
| 合格性层（Gate） | 这条视频能不能用 | 硬性规则 + 致命错误检测 | [docs/protocol.md](docs/protocol.md) |
| 能力诊断层（Diagnosis） | 好在哪里、差在哪里 | 六层维度评分 + 证据 | [docs/dimensions.md](docs/dimensions.md) |
| 版本决策层（Decision） | A 是否比 B 更好 | GSB Pairwise | [docs/protocol.md](docs/protocol.md) |

## 两种评估模式

| 模式 | 输入 | 可评范围 |
|---|---|---|
| 有参照（with-reference） | 视频 + Brief/产品事实/平台/品牌要求 | 全部六层 |
| 无参照（no-reference） | 只有视频 | 仅视频自身可观察的维度（L2–L5 全部，L1/L6 大部分不可评） |

无参照模式必须在报告中注明降级范围，不允许 Judge 脑补参照。

## 评估思路的三条支柱

1. **客观优先（双重评估）**：能用工具确定性测量的绝不交给 Judge——时长/比例/可播放用 ffprobe，错字用 OCR 比对，语言/事实用 ASR 对照，响度用 LUFS。Judge 只评工具测不了的主观维度。每个维度的客观/主观分工见 [docs/dimensions.md](docs/dimensions.md)。
2. **Judge 逼近人类偏好**：AI Judge 预测的是 P(目标人群更偏好 A | 任务, 约束, A, B)，不是绝对"视频真理"。实现上：类型路由前置（prompts/genre_router.md，按视频类型注入 rubric 与观众人格）+ 观众/质检双人格分离（观众通道答"值不值得看"，诊断通道答"差在哪"）。有效性靠人类黄金集双向校准（错杀率+放水率），见 [docs/calibration.md](docs/calibration.md)。
3. **Judge 自身也被评估和进化（棘轮机制）**：Judge prompt/rubric 版本化，每次改动必须在黄金集上测与人类的一致率——提升才保留，下降就回滚；单一变量迭代；评审独立，生成者不许自评。见 [docs/evolution.md](docs/evolution.md)。

## 目录结构

```
videobench/
├── README.md            本文件：总纲
├── CLAUDE.md            agent 操作说明
├── docs/
│   ├── dimensions.md    六层质量维度 taxonomy（评估维度的唯一权威定义，含客观/主观分工）
│   ├── protocol.md      Judge 四步流程 + Gate + GSB + 指标 + 风险控制
│   ├── calibration.md   人类黄金集校准与 Judge 有效性验证
│   ├── evolution.md     Judge 的进化机制：版本化、棘轮、回滚、反模式清单
│   └── models.md        Judge 模型选型（gemini-3.5-flash + doubao-seed-2-pro 双模型策略）与已知坑
├── schemas/             输入输出的 JSON Schema 契约
├── prompts/             三个 Judge 的 prompt 模板（gate / dimension / gsb）
├── goldenset/
│   ├── cases/           评测题目（有参照模式的任务参照）
│   └── annotations/     人类 G/S/B 与维度标注（校准 Judge 用）
└── runs/                每次评估运行的结果留档
```

## 方法论借鉴

- **VBench (arXiv:2311.17982)**：质量解耦为具体维度、每维配专属评测方法、用人类偏好逐维验证自动指标 → 诊断层沿用"解耦 + 逐维人类校准"，维度体系换成面向商业交付的六层（VBench 只覆盖 L2/L3）。
- **UVE-Bench (arXiv:2503.09949)**：pairwise 偏好标注含 same good/same bad（对应 S 档）；MLLM 单视频打分 vs 直接成对比较两种协议（后者难得多：强模型 ~51% vs 人类 88%）；换位一致性；抽帧数量显著影响时序判断 → GSB 层沿用其协议与偏差控制。
- **darwin-skill (github.com/alchaincyf/darwin-skill)**：度量-保留式进化——棘轮机制（只保留可度量的提升，失败回滚）、单一变量迭代、独立评审防自评偏差、双重评估（静态规则 + 运行时验证）、人类检查点、反模式清单 → 用于客观/主观分工和 Judge 自身的进化流程。
- **本地已有资产**：`~/Documents/视频调优工具包/视频调优工作簿.xlsx` 的 GoldenSet清单与 7 维评分卡是六层维度的前身，题目可迁入 `goldenset/cases/`。

## 核心原则

> 人类定义什么叫好，AI 负责把这个定义稳定地执行一万次；而 Judge 每一次变得更像人，都必须有黄金集上的数字为证。

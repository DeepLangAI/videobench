# VideoBench — Agent 操作说明

这是一个直接评估视频的 benchmark：输入是产出的成片（可附任务参照），输出是三级判定（Gate 能不能用 / 六层维度好在哪差在哪 / GSB 比基线如何）。**只评视频本身，不评生成系统**——成功率、耗时、成本属于生成链路（~/kuleshov）的监控，不在本项目范围。

## 不可违反的硬规则

1. **完整评估 = Gate + 多维诊断 + GSB**，不允许只跑一次 GSB 就出结论；
2. 维度定义唯一权威在 `docs/dimensions.md`，任何 prompt/schema/报告不得自造维度；
3. **客观优先**：能用工具确定性测量的（ffprobe 规格、OCR 错字、ASR 语言/事实、LUFS）不交给 Judge；客观轨与 Judge 冲突时以客观轨为准；
4. 每个分数、每个 fail、每个 GSB 结论都必须附可验证证据（时间戳/帧号/OCR-ASR 引文），没有证据的结论无效；
5. GSB 必须允许 S，且报告必须同时给三个指标：G/S/B 分布、Net Lift=(G−B)/N、Decisive Win Rate=G/(G+B)——只报其中一个即误导；
6. 成对评估必须随机化 A/B 位置、不透露哪个是新版本；重要样本换位复评，反转即标"不稳定"；
7. 美学不得覆盖任务完成度和事实错误；
8. 低置信度、换位冲突、Gate borderline 样本一律 needs_human=true，不许硬判；
9. 两种模式：with_reference（参照齐全才评，缺任一项拒评）/ no_reference（只评不需参照的维度，报告注明降级），**不允许 Judge 脑补参照**；
10. **Judge 自身的任何改动走进化流程**（docs/evolution.md）：单一变量、黄金集回归、提升保留否则回滚、独立评审、生成者不许自评、上线前人工确认；
11. **类型路由前置**：任何视频先过 prompts/genre_router.md 定类型/受众/类型语言，再注入对应 rubric——严禁一份 prompt 打天下（2026-07-15 实测同模型换口径 1.5→5.0 分）；
12. **观众/质检双人格分离**：观众反应通道（prompts/audience_judge.md，禁术语，答"值不值得看"）与专业诊断通道（答"差在哪"）并行互不污染，GSB 用户价值以观众通道为锚；
13. **黄金集回归必须双向**：错杀率 + 放水率同报，任一退步即回滚；严禁用"X 不算缺陷"式引导措辞修复错杀。

## 目录导航

- `docs/dimensions.md` 六层维度 taxonomy（L1 任务 / L2 视觉 / L3 时序 / L4 音频 / L5 叙事 / L6 商业），含每维的客观/主观分工与是否需参照
- `docs/protocol.md` 模式与客观轨、Judge 四步流程、Gate 八条规则、GSB 三层判断、三指标、五大风险控制、runs 留档结构
- `docs/calibration.md` 人类黄金集校准闭环、Judge 有效性六项检验
- `docs/evolution.md` Judge 进化机制：棘轮、回滚、单变量迭代、反模式清单
- `docs/models.md` Judge 模型选型：gemini-3.5-flash（全维度，唯一听得到音频）+ doubao-seed-2-pro（视觉专项交叉验证）双模型并行、合并规则、评分虚高 1–1.5 分的密度锚定校准、已知坑清单
- `schemas/` 输入输出契约（task_context / evidence / gate_result / dimension_scores / gsb_result）
- `prompts/` Judge 模板：genre_router（第0步类型路由）/ audience_judge（观众反应通道）/ gate / dimension / dimension_judge_showcase（showcase 类型 rubric）/ gsb
- `goldenset/` 题目与人类标注（annotations/ 含 2026-07-15 showcase 组顶级样本标注）；`runs/` 评估运行留档 + `runs/judge-versions.md` Judge 版本账本

## 关联资产

- 旧评分体系与 golden set 在 `~/Documents/视频调优工具包/视频调优工作簿.xlsx`（video-score / golden-set-regression / screening-review skills 围绕它工作）；旧 7 维 → 新六层映射见 dimensions.md 末尾；
- 方法论来源：VBench (arXiv:2311.17982)、UVE-Bench (arXiv:2503.09949)、darwin-skill (github.com/alchaincyf/darwin-skill)。

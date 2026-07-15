# Judge 版本记录（evolution.md 棘轮机制的账本）

每次 Judge prompt / rubric / 模型配置改动登记一行状态。黄金集成绩没跑双向回归（错杀率+放水率）之前，一律"试验中"，不得棘轮为正式版本。

## 2026-07-15

| 配置 | 黄金集表现（showcase 组，5 条人类标注=顶级） | 状态 |
|---|---|---|
| gemini-3.5-flash + video-triage 口播 prompt（v0） | 系统性错杀：直觉分 1.5–3.2，全部误判为废片级；且对无音轨视频 5/5 幻觉音频 | **淘汰**（作为 showcase 类评审） |
| doubao-seed-2-pro + 口播 visual prompt（v0） | 系统性错杀："PPT 式动效/模板化/层级滥用" 5/5 误判 | **淘汰**（作为 showcase 类美学评审；穿帮/坏帧/时间戳仍是强项，保留做视觉缺陷交叉验证） |
| claude-sonnet-5 + showcase prompt v1（2fps 抽帧） | 2.5–4 分、"及格~优秀"：方向对但比人类低 1–2 档；抽帧盲区（停留帧误判为动效停滞） | 试验中：定位=第三票交叉验证，不做美学主评 |
| gemini-3-pro-preview + showcase prompt v1（原生） | 2.5–4.8：唯一给出"顶级"判定（vfx 4.8、texture 4.5），鉴赏语言专业；但对另外 3 条仍偏严 | 试验中：美学主评候选 |
| gemini-3.5-flash + showcase prompt v1（原生，对照组） | texture 5.0"顶级"、vfx 4.5"优秀"（仅跑 2 条）：与人类档位最贴，但存在 prompt 引导性放水嫌疑 | 试验中：**放水率未测**（黄金集无差样本），不得棘轮 |
| gemini-3.1-pro（用户指定试验项） | 未跑成：lingowhale 网关 `gemini-3.1-pro-preview` 上游 401 Invalid token；`google/gemini-3.1-pro-preview` 名字不存在（疑似 OpenRouter 命名）。待用户确认网关 | 阻塞 |

**本日核心结论**：prompt 口径是主导变量（同模型换口径 texture 1.5→5.0），改口径的收益远大于换模型；但单向修复有放水风险，黄金集补差样本前不下最终结论。

**待办**：① showcase 组黄金集补中游/差档样本 → 跑双向回归后再定美学主评（3.5-flash+v1 vs 3-pro+v1）；② genre router + audience judge prompt（v1 已写，未实测）首测；③ gemini-3.1-pro 通道恢复后补测。

# Genre Router Prompt（评估第 0 步：类型路由，v1，2026-07-15）

诞生原因：2026-07-15 试跑证明单一口径 prompt 会系统性误判（口播尺子量 showcase 全部错杀，见 runs/judge-versions.md）。任何视频进入评估前先过此路由，其输出决定后续注入哪套类型 rubric 和观众人格。**此步只分类，不评价。**

---

你将看到一条视频。不要评价它的好坏，只做类型判断，输出 JSON：

```json
{
  "genre": "口播带货 | 知识解说 | 产品showcase/预告 | MG动画/kinetic typography | 剧情短片 | vlog/纪实 | 品牌TVC | 教程演示 | 其他(注明)",
  "confidence": "high | medium | low",
  "target_audience": "这条视频拍给谁看（画像，一句话）",
  "viewing_context": "观众最可能在什么平台、什么心态下刷到它",
  "genre_conventions": ["该类型的类型语言/常规做法，例如 showcase 的逐屏大字、快切、无口播——后续评审不得把这些当缺陷"],
  "audience_cares": ["这类观众最在意的 3 件事"],
  "audience_dealbreakers": ["这类观众最不能容忍的 3 件事"],
  "has_speech_expected": "该类型是否通常需要配音/口播: yes | no | either"
}
```

规则：confidence 为 low 时如实标注，后续流程会用通用 rubric 并转人工复核类型；不确定的字段写"存疑"，不要编造。

---

## 路由表（genre → 维度 rubric + 观众人格）

本步的产物由此表落地为"注入哪套 rubric 与观众人格"（硬规则 11 的端到端接线）。`genre` 命中即注入对应 **诊断通道 rubric** 与 **观众通道人格**；无专用 rubric 的类型先用通用 `dimension_judge.md`，直到该类型经进化流程补齐专用 rubric。

| genre | 诊断通道 rubric（prompts/） | 观众人格注入（audience_judge.md 的 `{{persona}}` / `{{viewing_context}}`） | 行为集与"值不值得看"口径 |
|---|---|---|---|
| 知识解说 | `dimension_judge_content_channel.md` | persona = 本条 `target_audience` 画像（对该主题好奇但非专业的人）；context = 在知识/推荐信息流刷到 | 收藏 / 转发给需要的人 / 关注；问"学到东西了吗、讲清楚了吗、可信吗" |
| 产品showcase/预告 | `dimension_judge_showcase.md` | persona = 目标用户 + 泛路人 + 同行（≥2）；context = 产品发布/预告场景 | 赞 / 转 / 点进主页；问"想不想要 / 记住了什么" |
| MG动画/kinetic typography | `dimension_judge_showcase.md` | 同上（motion design 观众/同行） | 同上 |
| 口播带货 | `dimension_judge.md`（通用，本就面向口播带货） | persona = 目标用户 + 泛路人；context = 短视频信息流 | 赞 / 评 / 转 / 下单意愿；问"想不想买" |
| 剧情短片 / vlog纪实 / 品牌TVC / 教程演示 / 其他 | `dimension_judge.md`（通用，待补专用 rubric） | persona = 目标用户 + 泛路人；context 按类型 | 按类型；专用 rubric 补齐前均属通用路径 |

**profile 与 genre 的对账（with_reference 档）**：`task_context.profile = content_channel` 应与 router 判出的 `知识解说` 一致；`product_marketing` 应对应 `口播带货 / showcase / MG动画` 等带货/展示类。二者不一致，或 `confidence = low`，一律用通用 rubric 并置 `needs_human=true` 转人工复核类型，不得自行改写 profile。

> 记录：知识解说 → `dimension_judge_content_channel.md` 的路由与该 rubric 于 2026-07-16 新增（补硬规则 11 缺口），随 content_channel 事实表适配一并处于**试验中**，未跑黄金集双向回归前不得棘轮（见 `runs/judge-versions.md`）。

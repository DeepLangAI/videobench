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

## 2026-07-16

| 配置 | 变更（单一逻辑变量：为新 profile 接通事实表参照） | 状态 |
|---|---|---|
| task_context content_channel 档 + gate_judge / dimension_judge / dimensions.md / dimension_scores.schema | ① schema 新增 content_channel profile（channel/query/must_cover/key_facts/research_notes）；② dimensions.md L1（信息准确/内容完整/指令遵循）事实表口径由 product_facts 泛化为 product_facts / key_facts / must_cover，并加"未核验 key_facts→needs_human"门槛；③ gate_judge 规则 2、3 与 dimension_judge L1 均改为 profile-aware：content_channel 读 key_facts/must_cover，且 verified_by_human=false 的 key_facts 冲突/缺失→needs_human、不硬判 fatal；④ dimension_scores.schema 增 needs_human 字段承载该规则 | **试验中**（未棘轮） |

**说明**：
- **向后兼容**：product_marketing / 无 profile 路径行为不变，现有黄金集（showcase 组，2026-07-15）不受影响，无回归风险；改动仅新增 content_channel 分支与可选字段（needs_human）。
- **未核验事实表的安全门槛贯通 Gate 与维度两层**：content_channel 的 key_facts 为 AI 起草（verified_by_human=false），Gate 与 dimension_judge 一律不得据此硬判致命/fatal，只置 needs_human——避免用未经人工核验的事实表做高风险裁决（硬规则 4/8）。
- **双向回归待补**：content_channel 目前无成片、无人类标注，错杀率/放水率无法测；按本账本规则「没跑双向回归一律试验中」，**不得上线为正式版本**。需先为 goldenset/cases/case-001~006 产出成片 + 补一小批人类判定（goldenset/annotations/），再跑双向回归后方可棘轮。
- **已知缺口（棘轮前补齐）**：genre_router 虽有"知识解说"类型，但尚无从 content_channel 路由到专用维度 rubric 的落地（现仅有 dimension_judge_showcase.md）——硬规则 11 的路由→rubric 端到端接线未完成；platform_requirements 为承载 content_channel 的 null 桩对所有 profile 放宽（仅放宽未收紧，Gate 规则 8 行为不变）。
- **独立评审（生成者不自评）**：本次 diff 经独立 subagent 评审——首轮 BLOCK（维度打分层 dimension_judge.md 未接入"未核验→needs_human"例外，与 Gate/schema 承诺冲突），已修复（dimension_judge.md + dimension_scores.schema + dimensions.md 补齐）后复审；结论以独立评审为准，非生成者自行宣布有效（无黄金集数字，不作"改进有效"声明）。
- **人类检查点**：涉及 Gate 规则 2/3 修改（属"Gate 规则增删改"强制人工确认项）——由用户在本次会话中授权发起，正式棘轮仍需回归数字 + 抽查误判样本。

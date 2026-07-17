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

### 2026-07-16（补接线，承接上条，仍未棘轮）

| 配置 | 变更（单一逻辑变量：补齐硬规则 11 的路由→rubric 端到端接线） | 状态 |
|---|---|---|
| genre_router 路由表 + `prompts/dimension_judge_content_channel.md`（新）+ audience_judge 知识类口径注入 | ① 新增 content_channel 专用维度 rubric（对齐 dimensions.md 六层、不新增维度；把"未核验 key_facts→needs_human 不硬判"门槛落到打分层；用中性档位锚定而非"X 不算缺陷"式豁免，避开反模式 #9）；② genre_router 增路由表：知识解说→content_channel rubric + 知识类观众人格，并规定 profile↔genre 对账不一致/低置信→needs_human；③ audience_judge 增知识类"值不值得看"口径（学到没/可信否，行为看收藏转发） | **试验中**（未棘轮） |

**说明**：
- **向后兼容（精确版）**：路由表对 showcase / 口播带货 / 通用路径只做**现状描述**，不改其行为；新增仅"知识解说→新 rubric"一条分支与新文件。`audience_judge.md` 是跨类型共享 prompt、本次加了一段知识类口径注入——它逻辑上只作用于知识解说人格，但物理上对所有类型可见；2026-07-15 showcase 黄金集是**诊断/视觉基线、不调用 audience 通道**（该通道"v1 已写、未实测"），故 showcase 黄金集确实不受影响。audience 通道尚无 baseline，其回归随 content_channel 首测一并建立——因此不宣称"全局无回归风险"，只说"现有 showcase 诊断黄金集不受影响"。
- **单变量归因的边界**：本条虽定位为一个"逻辑变量"（补接线），实际动了 3 个资产（路由表 + 新 rubric + audience 注入）。因是 0→1 净新增路由、未扰动既有行为，暂不违反棘轮，但 Step-D 回归须知：该组分数若变化，**无法在三资产间归因**——如需归因，回归时分别开/关三者。
- **仍不得棘轮**：本条补的是"棘轮前缺口"，非回归证据。content_channel 仍无成片、无人类标注，**错杀率/放水率仍无法测**；接线完成 ≠ 有效性已证。生成者（本次接线的作者）不得自行宣布"改进有效"（evolution.md 第 4 条）。

### 棘轮门禁清单（content_channel：试验中 → 正式，逐项需人工，勿跳步）

按 evolution.md 棘轮机制与 CLAUDE.md 硬规则 10/11/13，下列全部完成前一律"试验中"：

- [ ] **A. 成片**：为 case-001~006 产出成片。**已定：先每题一条起步**（2026-07-16 用户决定）。⚠️ 单条/单档**测不出放水率**（放水需差/致命样本）——分档样本（顶级/中游/差 + 致命，calibration.md 档位矩阵）为后续补齐项；补齐前 Step D 只能报错杀率一侧，报告须注明"放水率暂缺、结论不完整"，且**在双向都能测之前不得棘轮**（硬规则 13）。
- [ ] **B. key_facts 人工核验**：把已核验的 key_facts 在 case JSON 中置 `verified_by_human=true`（**case-003 必须按发布日复核条款**）。核验前事实冲突只能是 needs_human，不能作判分依据。
- [ ] **C. 人类标注入库**：≥2 名标注员按 `goldenset/annotations/_content-channel-annotation-template.md` 标注、分歧仲裁，存入 `goldenset/annotations/`。
- [ ] **D. 双向回归**：跑 content_channel 组，**同时报错杀率 + 放水率 + GSB 三分类一致率 + Gate 致命召回率**；任一退步即回滚。严禁用引导性措辞修错杀（反模式 #9）。
- [ ] **E. 独立评审**：回归数字由独立运行给出，生成者不自评；抽查 needs_human 与误判样本。
- [ ] **F. Gate 规则 2/3 人工确认**：evolution.md「Gate 规则增删改」强制人工确认点，看回归 + 抽查后由人类**明确签字确认**（记录确认人/日期/结论）。
- [ ] **G. 棘轮**：以上齐备且回归为"提升"，才把 2026-07-16 两条从"试验中"改为正式版本，并记版本号 + 成绩 + 改了什么。

> 现状：Step 1（接线，A 之外的基础设施）已完成；A–G 中除本会话已发起的授权外，**均为人工闭环，AI 不代做**（尤其 B/C/F 是硬性人类检查点，D/E 依赖 B/C 的人类 ground truth）。

### 2026-07-17（gpt5.6-sol vs gpt5.5 盲评 run 中的 run 级校准实验，未棘轮）

| 配置 | 变更（run 级 prompt 装配，未改 prompts/ 下任何文件） | 状态 |
|---|---|---|
| `prompts/dimension_judge_content_channel.md` v2 + `docs/dimensions.md`（AI味/PPT味口径）+ `docs/models.md`（坑 #10-12）+ `docs/protocol.md`（抽帧复核台账）+ `prompts/gsb_judge.md`（调用方职责） | ① **顶级锚定**：注入"人类标注顶级商业作品=5 分锚 + 幻灯片式 AI 片 L2/L5 先验 2.5–3.5"；② **AI味/PPT味计扣**（用户明确要求）：作为 L2 美学/文字质量与 L5 节奏/信息层级的证据类别（不新设维度）；③ **密度锚定强制化**："先数确认问题（含时间戳）后按密度表给分"；④ **抽帧复核台账轨**：orchestrator 0.5fps 全片拼图人工复核 → objective/frame_review_ledger.json 注入 judge 作确认问题清单（客观优先） | **已写入正式资产**（2026-07-17 用户授权直写；黄金集双向回归仍为待办——showcase 组测错杀率 / content_channel 组测放水率，任一退步即回滚本条全部变更） |

**背景与证据**：首轮（dim2/gsb2）被人类标注人（用户）判定系统性虚高——003-a 全程 PPT 判 4.85/优秀、001-b 多处画面 bug 判 4.69/优秀、005 明显 a≫b 但均分 b>a。抽帧复核证实：双模型在 0.5fps 下漏掉 001-b 的空面板/悬浮元素/裁切残线/灰行叠压（全部人工确认有时间戳）。严格轨后：003-a→3.94、001-b→3.25（GSB 随之反转为 a 优且换位一致）、005 a 4.82 vs b 3.55，与人类判断对齐。
**已知风险**：校准块含"多数应落 2.5–3.5"先验，存在把真顶级样本错杀的反向风险（反模式 #9 的镜像）——上黄金集双向回归（错杀率+放水率同报）前不得进 prompts/ 棘轮；showcase 组（人类标注=顶级）是现成的错杀率测试集，content_channel 组放水率测试依赖门禁清单 A–C。
**新增已知坑（候选进 models.md）**：gemini 双视频同请求输入偶发把两条内容混为一条流（本 run case-005 首轮 GSB"拼接残损"说被抽帧证伪）；缓解=强制 duration_check + 换位复评 + 客观轨仲裁。

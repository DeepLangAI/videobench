### 逐层质量诊断

#### L1 任务层（Task Alignment）
*   **指令遵循**：打分：`2` | `fatal_flag: true`
    *   **证据**：视频完全未提及并展示“未知生物的比例/尺度这一维度”，这是频道描述（`channel.description`）及 `must_cover` 中明确要求必须出现的关键点（`must_appear: true`）。这属于指令遵循的致命性缺失。
*   **信息准确 ⚑**：打分：`4` | `needs_human: true`
    *   **证据**：物理数值描述基本准确（如 00:05“每下潜10米，身上就多压一层大气”；00:10“30米约4atm，100米约11atm”包含海面1层空气，算术严谨）。但未提及未核验事实表中的 `key_fact 8`（深海低温约4°C），需要人工核验本期是否必须强制包含该温度维度。
*   **内容完整 ⚑**：打分：`2` | `fatal_flag: true` | `needs_human: true`
    *   **证据**：同“指令遵循”，缺少“未知生物的比例/尺度”这一核心必载内容。

#### L2 视觉层（Visual Quality）
*   **清晰度**：打分：`5`
    *   **证据**：1080P分辨率，图表边缘清晰，无压缩伪影。
*   **美学**：打分：`3`
    *   **证据**：虽然深青细线仪表风格与深海主题较贴合，但整体为典型的 AI 幻灯片模板配色与卡片堆砌，缺乏深度定制感。此外，`~00:40` 处整屏内容在切换时呈现明显的半透明残影状态（长交叉溶解重叠，持续时间 ≥2s），属于低级视觉瑕疵。
*   **主体质量 ⚑**：打分：`5`
    *   **证据**：全片无真人出镜，动态几何图形无变形或崩坏。
*   **文字质量**：打分：`4`
    *   **证据**：画面文字排版规范，但 `~00:40` 交叉溶解时旧字与新字重叠，极大地影响了短暂的可读性。

#### L3 时序层（Temporal Quality）
*   **人物一致性 ⚑**：`skipped_no_reference: true`
*   **物体恒常性**：打分：`5`
    *   **证据**：图形元素运动路径正常，无凭空闪现或消失的异常。
*   **运动自然**：打分：`3`
    *   **证据**：动画节奏单一，单屏画面静置长达 8-10s（如 00:20-00:30），且转场多依赖简单的淡入淡出，呈现明显的 PPT 翻页节奏，缺乏流畅的视线引导。
*   **无闪烁**：打分：`4`
    *   **证据**：无帧间突变闪烁，但 `~00:40` 的超长重叠过渡对视觉流畅度造成干扰。

#### L4 音频层（Audio Quality）
*   **音质**：打分：`4`
    *   **证据**：音轨正常存在，平均响度为 -18.4 LUFS（略低但合规），无爆音或杂音。
*   **语音准确 ⚑**：打分：`5`
    *   **证据**：AI 旁白配音发音清晰，普通话标准，无错字读音。
*   **音画同步**：打分：`5`
    *   **证据**：旁白、字幕与画面的出场点同步精确。
*   **音乐适配**：打分：`5`
    *   **证据**：背景选用低沉舒缓的氛围音效，烘托了深海的压迫感，且未掩盖人声。

#### L5 叙事层（Narrative）
*   **开头吸引力**：打分：`4`
    *   **证据**：00:00-00:03 以“你害怕的不是海水本身，而是深度把熟悉尺度全部重写”开篇，迅速切入心理感知层面，建立了较好的知识观看动机。
*   **镜头逻辑**：打分：`3`
    *   **证据**：从压力到光照再到心理机制的逻辑链合理，但镜头转场方式（如 00:40 的长残影过渡）生硬，且多以静态卡片展示为主，缺乏镜头推拉等叙事性视觉动效。
*   **节奏**：打分：`3`
    *   **证据**：画面信息密度偏低，视觉元素停留时间过长（如 30m 与 100m 压力对比画面从 00:09 持续静置至 00:19），节奏较为拖沓。
*   **信息层级**：打分：`3`
    *   **证据**：圆角卡片、不同颜色数值的堆砌感较强，视觉焦点在多张卡片并列时不够突出，信息呈现平面化。

#### L6 商业层（Commercial Usability）
*   **品牌一致性 ⚑**：`skipped_no_reference: true`
*   **卖点表达**：打分：`3`
    *   **证据**：虽然科普了压力和光线衰减，但因缺失“未知生物尺度”核心维度，导致频道的核心定位卖点未能完全展示。
*   **平台适配 ⚑**：打分：`5`
    *   **证据**：16:9 横屏规格，时长 64 秒，字幕完备。
*   **可交付性**：打分：`2`
    *   **证据**：由于核心内容缺失及视觉残影问题，无法直接交付，必须返工重制。

---

### 总体诊断与档位

*   **总体一句话诊断**：视频通过仪表风可视化较好地呈现了压力和黑暗维度，但严重遗漏了频道必载的“未知生物比例/尺度”维度，且中段出现长达 2 秒以上的重叠画面残影，整体呈现单调的 PPT 幻灯片节奏。
*   **直觉分**：`3.0`
*   **档位判断**：`差`（因核心内容维度严重缺失且伴随明显视觉瑕疵，无法直接发布，必须返工）
*   **needs_human 清单**：
    1.  **未核验 Key Fact 8 缺失核对**：
        *   *Fact 原文*：“深海（约 200 米以下）水温很低，平均仅约 4°C... 接近但仍高于海水冰点。”
        *   *成片引文*：完全未提及温度这一物理维度。需要人工确认在“深海恐惧症科普”主题下，未核验的事实 8（温度）是否为本期必须补充的内容。

---

### 机器可读输出

```json
{
 "scores": [
  {
   "layer": "L1_task",
   "dimension": "指令遵循",
   "method": "judge",
   "score": 2,
   "evidence": [
    {
     "timestamp_sec": 40.0,
     "description": "视频从压力和黑暗直接跳入心理恐惧机制，全片完全未包含『未知生物的比例/尺度』维度，未满足频道描述要求。"
    }
   ],
   "fatal_flag": true,
   "needs_human": false
  },
  {
   "layer": "L1_task",
   "dimension": "信息准确",
   "method": "judge",
   "score": 4,
   "evidence": [
    {
     "timestamp_sec": 10.0,
     "description": "物理量计算正确，但事实表中未核验的深海低温（Fact 8）未在片中体现，标记为 needs_human。"
    }
   ],
   "fatal_flag": false,
   "needs_human": true
  },
  {
   "layer": "L1_task",
   "dimension": "内容完整",
   "method": "judge",
   "score": 2,
   "evidence": [
    {
     "timestamp_sec": 45.0,
     "description": "缺失『未知生物的比例/尺度』这一 channel.description 指定的 must_cover 点，以及未核验的低温事实点。"
    }
   ],
   "fatal_flag": true,
   "needs_human": true
  },
  {
   "layer": "L2_visual",
   "dimension": "清晰度",
   "method": "judge",
   "score": 5,
   "evidence": [
    {
     "timestamp_sec": 20.0,
     "description": "画面分辨率高，图表及文字无模糊或压缩伪影。"
    }
   ]
  },
  {
   "layer": "L2_visual",
   "dimension": "美学",
   "method": "judge",
   "score": 3,
   "evidence": [
    {
     "timestamp_sec": 40.0,
     "description": "从00:39到00:41，画面在进行长交叉溶解过渡时，旧卡片与新卡片内容发生长时间的半透明重叠叠加，产生明显残影瑕疵。"
    }
   ]
  },
  {
   "layer": "L2_visual",
   "dimension": "主体质量",
   "method": "judge",
   "score": 5,
   "evidence": [
    {
     "timestamp_sec": 15.0,
     "description": "无真人出镜，几何动效及图表元素未见变形。"
    }
   ]
  },
  {
   "layer": "L2_visual",
   "dimension": "文字质量",
   "method": "judge",
   "score": 4,
   "evidence": [
    {
     "timestamp_sec": 40.0,
     "description": "~40s 残影过渡期，新旧卡片文字重叠粘连，短期内严重干扰阅读。"
    }
   ]
  },
  {
   "layer": "L3_temporal",
   "dimension": "人物一致性",
   "skipped_no_reference": true
  },
  {
   "layer": "L3_temporal",
   "dimension": "物体恒常性",
   "method": "judge",
   "score": 5,
   "evidence": [
    {
     "timestamp_sec": 30.0,
     "description": "图表元素过渡顺畅，没有无故的闪现或消失。"
    }
   ]
  },
  {
   "layer": "L3_temporal",
   "dimension": "运动自然",
   "method": "judge",
   "score": 3,
   "evidence": [
    {
     "timestamp_sec": 20.0,
     "description": "单屏卡片静置长达8-10秒，动效以淡入淡出为主，动态交互感极弱，呈PPT平铺节奏。"
    }
   ]
  },
  {
   "layer": "L3_temporal",
   "dimension": "无闪烁",
   "method": "judge",
   "score": 4,
   "evidence": [
    {
     "timestamp_sec": 40.0,
     "description": "画面无高频闪烁，但40s处交叉溶解时间过长影响了时序过渡的平滑性。"
    }
   ]
  },
  {
   "layer": "L4_audio",
   "dimension": "音质",
   "method": "judge",
   "score": 4,
   "evidence": [
    {
     "timestamp_sec": 10.0,
     "description": "音轨存在且完整，无杂音底噪，整体响度正常。"
    }
   ]
  },
  {
   "layer": "L4_audio",
   "dimension": "语音准确",
   "method": "judge",
   "score": 5,
   "evidence": [
    {
     "timestamp_sec": 5.0,
     "description": "普通话配音，发音清晰，无读音错误。"
    }
   ]
  },
  {
   "layer": "L4_audio",
   "dimension": "音画同步",
   "method": "judge",
   "score": 5,
   "evidence": [
    {
     "timestamp_sec": 25.0,
     "description": "旁白提及的深度数值与屏幕仪表盘动效、字幕完全同步。"
    }
   ]
  },
  {
   "layer": "L4_audio",
   "dimension": "音乐适配",
   "method": "judge",
   "score": 5,
   "evidence": [
    {
     "timestamp_sec": 15.0,
     "description": "低沉压抑的背景音乐与深海压迫感主题极其贴合。"
    }
   ]
  },
  {
   "layer": "L5_narrative",
   "dimension": "开头吸引力",
   "method": "judge",
   "score": 4,
   "evidence": [
    {
     "timestamp_sec": 0.0,
     "description": "以‘你害怕的不是海水本身’开篇，引入尺度改写，快速形成科普吸引力。"
    }
   ]
  },
  {
   "layer": "L5_narrative",
   "dimension": "镜头逻辑",
   "method": "judge",
   "score": 3,
   "evidence": [
    {
     "timestamp_sec": 40.0,
     "description": "镜头为PPT式的直接切页，~40s处的长残影过渡暴露了剪辑粗糙，缺乏流畅的视线引导。"
    }
   ]
  },
  {
   "layer": "L5_narrative",
   "dimension": "节奏",
   "method": "judge",
   "score": 3,
   "evidence": [
    {
     "timestamp_sec": 15.0,
     "description": "每一页信息停留时间过长，动效元素少，整体节奏偏拖沓、AI感重。"
    }
   ]
  },
  {
   "layer": "L5_narrative",
   "dimension": "信息层级",
   "method": "judge",
   "score": 3,
   "evidence": [
    {
     "timestamp_sec": 30.0,
     "description": "并排的卡片式信息呈现扁平，视觉上只是字号/颜色对比，缺乏由主到次的视觉动效引导。"
    }
   ]
  },
  {
   "layer": "L6_commercial",
   "dimension": "品牌一致性",
   "skipped_no_reference": true
  },
  {
   "layer": "L6_commercial",
   "dimension": "卖点表达",
   "method": "judge",
   "score": 3,
   "evidence": [
    {
     "timestamp_sec": 50.0,
     "description": "因为缺失了『未知生物的比例』这一频道核心亮点，卖点传达不完整。"
    }
   ]
  },
  {
   "layer": "L6_commercial",
   "dimension": "平台适配",
   "method": "judge",
   "score": 5,
   "evidence": [
    {
     "timestamp_sec": 60.0,
     "description": "16:9 横屏视频，时长符合规范，有完整中文字幕。"
    }
   ]
  },
  {
   "layer": "L6_commercial",
   "dimension": "可交付性",
   "method": "judge",
   "score": 2,
   "evidence": [
    {
     "timestamp_sec": 45.0,
     "description": "由于缺失了核心内容维度且有明显的长溶解残影视觉缺陷，不合格，无法直接交付。"
    }
   ]
  }
 ],
 "one_line_diagnosis": "视频通过仪表风可视化较好地呈现了压力和黑暗维度，但严重遗漏了频道必载的“未知生物比例/尺度”维度，且中段出现长达2秒以上的半透明画面残影，整体转场和动效呈现明显的PPT式单调节奏。",
 "intuition_score": 3.0,
 "tier": "差",
 "needs_human_items": [
  {
   "reason": "成片完全未提及深海的温度这一重要环境物理量，需核对是否属于必须呈现的关键物理背景事实。",
   "key_fact": "深海(约 200 米以下)水温很低，平均仅约 4°C(39°F)；最深处(如 5000 米实测)约 2°C，接近但仍高于海水冰点，故保持液态而非结冰。",
   "video_quote": "无（片中仅介绍了压力、光照维度）"
  }
 ]
}
```
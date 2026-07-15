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

# 复核回桶票 0005

在「回桶分料」筛选 A12。入罐见票 0001、0002，分别为铁红 100 g 和钛白 200 g。上件净重 120 g 后各剩 60 和 120 g，损耗净量 30 g 后各剩 50 和 100 g。称量票 0005 毛重 140 g 减去皮重 20 g，120 g 按 1:2 分成 40 和 80 g。罐内剩余 10 和 20 g，分别进入争议列。

证据下载包含原始 `sheets`、工单 `manifest` 和逐站 `snapshot`。`recovery.rows` 可按票号找 `parts_mg`、`before_mg` 与 `after_mg`，入罐行见 `issue_lines`，皮重版本见 `tares`。`balance.lines` 对照实际回桶数、申报和两者差额。摘要可对 `manifest`、`sheets`、`snapshot` 对象的 UTF-8 JSON 计算 SHA-256，键递归排序、中文保留、逗号冒号省略空白。

## 同分钟先后不定时

旧秤只到分钟，同一罐里同刻的领用与上件可能分不清先后。凭证不再只给一套配比：`recovery.rows` 的 `parts_mg` 是基准方案（先出罐后入罐）的实数，`parts_range_mg` 是全部可行方案的区间，`uncertain_mg` 是仍未定的重量，`provisional` 标记该票不可当实数用。`recovery.ambiguity` 列出无法分辨的分钟与原件行，`scenarios` 记每个罐的可行方案数；`truncated` 为真时可行方案过多，区间只覆盖预算内抽到的方案，并保留两端，实际范围可能更宽。

证据里的 `uncertainty` 是给复核人的汇总：`lines` 逐批号列出未定区间与申报对照，`recovery` 逐票列出仍带区间的分摊与先后标记，`ambiguity`、`scenarios`、`truncated` 照抄复算结果。区间内的重量是可行范围，签发时随摘要一并封存，供后续回桶沿区间复算。

`balance.lines` 的 `range_mg` 给出该批号各项区间，`difference_range_mg` 是申报差额区间。申报落在区间内时 `code` 为 `UNCERTAIN`、`difference_mg` 为 `None`；即使恰好相等也不签 `MATCH`。`check_range_mg` 应是 `[0,0]`，表示每个可行方案都勾稽平。证据里的 `uncertainty` 汇总这些未定项，便于复核人先看区间再审实数。

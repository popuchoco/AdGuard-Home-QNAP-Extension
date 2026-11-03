# Architecture

## 目標

Extension 是一個由單一 ARMv7 Go binary 提供的 read-only dashboard。它不取代 AdGuard Home、Uptime Kuma、QTS 或 QuRouter 的管理頁，也不把其中一套 API 假裝成另一套。核心目標是在資源有限的 NAS 上，用可預測的 CPU、RAM、I/O 與連線數提供足以判斷狀態的摘要。

## 元件

### Embedded static UI

透過 Go `embed` 與 API 放在同一個 binary，只讀取同源 JSON，不知道任何上游帳密。UI 顯示來源、觀測時間、資料年齡與限制；單一來源故障不會清空其他卡片。

### Go API

負責 schema、authentication boundary、cache 與 refresh coordination。API handler 不直接同步查詢上游；它讀取 snapshot，因此 response latency 不依賴 NAS 當下速度。整個 process 必須能在 48 MB container limit 下運行。

### Collectors

AdGuard、Uptime Kuma 與 QTS collector 各自擁有 timeout、TTL、backoff 與 circuit state。QuRouter v1 不直接登入，而是重用 Kuma 的 QHora Ping／Web heartbeat。Collector 只能呼叫 source-specific allowlist，不能接受使用者提供 URL。

### Snapshot cache

每個來源保存最後成功資料、最後嘗試時間、錯誤與 schema version。失敗時保留 last-known-good 並標示 `stale`，不以空物件覆蓋。

## 資源控制

- 固定 worker 數：正常情況三個 source 最多各一個 request chain。
- Single-flight：同一來源 refresh 期間的新請求共用結果。
- TTL tiering：slow storage probe 不跟 fast DNS status 同頻率。
- Adaptive interval：RAID 只有在 recovery/resync 時提高頻率。
- Payload cap：events、clients、query log 都限制筆數與 bytes。
- Streaming decode：避免先保留一份 response bytes 再建立完整 DOM；XML parser 必須有 size limit。
- No time-series database：Extension 只保留短期 snapshot；長期歷史交給 Prometheus、InfluxDB 或外部監控。
- No query-log replication：只讀聚合 stats，避免複製 AdGuard Home 大量明細。
- Hard memory budget：Container/QPKG 目標常態 10–30 MB，上限 48 MB。
- One binary：前端、API 與 scheduler 不拆成 Node frontend 加 backend 兩個 runtime。

## QTS collector

QTS collector 先登入取得 SID，批次完成 CGI reads，再依有效期短暫重用。資料分層：

1. system：model、firmware、uptime、CPU、memory、temperature。
2. storage summary：volume、bay、top-level SMART health。
3. deep read-only probes：`/proc/mdstat`、固定 QPKG metadata。

已知限制必須保留在輸出：固定 volume index coverage、unknown status code、SMART attributes unavailable、QNAP 128-wide md bitmap。SSH 只允許固定 argv，不允許 shell、任意 path 或任意 package。

## Uptime Kuma collector

讀取既有 Status Page config 與 heartbeat，呈現 QHora Ping、QuRouter Web、QTS、AdGuard DNS／Web 的可用性與延遲。這讓 Extension 不必重複開 Ping、HTTP 與 DNS probes，也保留 Kuma 的歷史及 Telegram 通知。

## QuRouter boundary

原始 v1 不包含直接 QuRouter collector。它只讀取 Kuma 已測得的路由器存活結果，並提供管理頁連結。

深度 QuRouter collector 是後續選用功能；若實作，必須是完全獨立的 auth state machine：

1. 以 `force=false` 登入。
2. 若取得 token，依 action allowlist 查詢。
3. 在 `finally` logout。
4. 若裝置回報 existing session 且沒有 token，停止查詢，回報 `busy_active_session`。

Clients 與 events 是較昂貴資料，只能 opt-in、使用較長 TTL、限制筆數，且可設定成僅手動 refresh。QuRouter token 不進入共享 QTS cache。

## Failure model

| 情況 | 行為 |
|---|---|
| 上游 timeout | 回傳 last-known-good + `stale`，並 exponential backoff |
| 認證失敗 | `unavailable`，不無限重試，不洩漏 response body |
| Parser 未知格式 | `indeterminate` + raw status code/fixture request |
| QuRouter active session | `busy_active_session`，不 force login |
| Bridge cold start | 各來源 `unavailable`，collector 非同步暖機 |
| 單一來源 circuit open | 其他來源持續更新 |

## Deployment boundary

Bridge 應與 AdGuard Home 位於同一 NAS 或受信任管理網段，但使用獨立 process/container。Reverse proxy 負責 TLS 與登入入口；Bridge 仍需驗證 forwarded identity 或專用 API token，不能只因為位於 LAN 就完全公開。

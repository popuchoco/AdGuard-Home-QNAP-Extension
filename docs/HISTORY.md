# Design history

## 2026-09-16：原始需求

需求是把 AdGuard Home、Uptime Kuma、QTS 與 QuRouter 集中到一個私人首頁，並直接顯示 AdGuard 與 QNAP device 狀態。

最先評估的是 Homepage，但 TS-431K 使用 32-bit ARMv7，當時 Homepage 官方映像只支援 AMD64／ARM64；使用停止更新的舊 ARMv7 映像會帶來維護與憑證風險。NAS 實測約 1 GB RAM、可用記憶體約 285 MB、Swap 約已使用 775 MB，因此也不適合在 NAS 上自行建置及常駐完整 Next.js stack。

## 原始替代設計

提出一個單一 ARMv7 Go 程式：

- Go `embed` 包入靜態 HTML／CSS／JavaScript。
- 記憶體目標 10–30 MB，container hard limit 48 MB。
- 閒置 CPU 接近 0%，每 60 秒更新一次。
- 不使用 DB、Node.js、Chromium 或 Docker socket。
- 只綁 Tailscale，憑證留在 server side。
- AdGuard：運作狀態、DNS 查詢數、封鎖數、比例。
- Uptime Kuma：服務可用性、入口與 heartbeat。
- QTS：CPU、RAM、磁碟容量、uptime 與入口。
- QuRouter：第一版只做 HTTP／Ping 存活狀態與入口。
- UI：四張綠／黃／紅狀態卡、responsive layout、dark mode。

## 當時的部署決策

進一步比較後，既有 Uptime Kuma 增加幾個 monitor 的額外成本低於新增一個 Dashboard，因此先完成了 Kuma Status Page：

- 網路：QHora Ping、QuRouter Web。
- NAS：QTS。
- 服務：AdGuard DNS、AdGuard Web。
- AdGuard Web 卡片可點擊進入管理頁。

Kuma 解決的是可用性監測、歷史、延遲與通知；它無法顯示 AdGuard 的查詢／封鎖統計或 QTS CPU／RAM／Storage 深度資料。完整 Go Dashboard 因此被保留為後續設計，而非當時已部署的服務。

原始工作目錄後來找回當日的 Kuma 設定腳本、資料庫備份及四版前端 bundle；最後一版只在 Kuma 管理選單加入指向 `/status/home-network` 的「詳細」連結。因原檔包含私人位址與明碼憑證，repository 僅保存去識別、環境變數化的重建版本與靜態預覽，不提交資料庫或原始 bundle。任何當時使用過的密碼都應視為已暴露並輪替。

## 本 repository 的定位

這裡保存的是上述未部署網頁擴充的可實作規格。未來若開始寫程式，v1 必須先忠於原始低耗用邊界；QuRouter clients、events、WAN、ports 等深度 API 應列為選用擴充，不得冒充最初已完成的功能。

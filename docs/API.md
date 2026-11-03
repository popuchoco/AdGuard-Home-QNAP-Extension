# API integration contract

## Extension API

所有時間使用 UTC RFC 3339。`status` 是資料狀態，不是 HTTP status 的替代品。

### `GET /extension/api/v1/summary`

一次回傳三個獨立來源的快照：

```json
{
  "schema_version": 1,
  "generated_at": "2026-11-04T00:00:00Z",
  "sources": {
    "adguard": {"status": "ok", "observed_at": "...", "age_seconds": 5, "data": {}},
    "qts": {"status": "indeterminate", "observed_at": "...", "age_seconds": 20, "data": {}, "limitations": []},
    "qurouter": {"status": "busy_active_session", "observed_at": "...", "age_seconds": 65, "data": {}}
  }
}
```

### `GET /extension/api/v1/sources/{source}`

`source` 只能是 `adguard`、`qts`、`qurouter`。不得接受任意 hostname 或 upstream URL。

### `POST /extension/api/v1/refresh/{source}`

排程 refresh，回傳 `202 Accepted`。若已在執行則回傳相同 job；若 cooldown 尚未結束，回傳 `429` 與 `Retry-After`。

## AdGuard Home upstream

| 用途 | Endpoint | 正規化輸出 |
|---|---|---|
| DNS service | `GET /control/status` | running、protection、version、addresses |
| rolling statistics | `GET /control/stats` | queries、blocked、avg processing time |

使用官方 HTTP API 的 Basic Auth。Bridge 不代理任意 `/control/*` endpoint，也不長期保存 query log 明細。

## QTS upstream

| 用途 | Endpoint/Probe | 備註 |
|---|---|---|
| authentication | `/cgi-bin/authLogin.cgi` | 取得短期 `authSid`，不回傳 UI |
| system | `/cgi-bin/management/manaRequest.cgi?subfunc=sysinfo` | model、firmware、uptime、temperature |
| volume | `/cgi-bin/disk/disk_manage.cgi?func=extra_get&extra_vol_index=1` | coverage 必須標記 unverified |
| SMART summary | `/cgi-bin/disk/qsmart.cgi?func=all_hd_data` | top-level summary 不等同完整 attributes |
| RAID | fixed SSH `cat /proc/mdstat` | QNAP 128-wide map 保留 unknown semantics |
| QPKG | fixed `/sbin/getcfg` fields | Enable/Status 不代表 daemon/workload healthy |

有 2FA 的帳號需要部署環境提供短期 security code 或改用專用唯讀帳號；Extension 不保存可繞過 2FA 的 token。

## QuRouter upstream

Base URL 範例：`http://router.example/miro/api`。

| 用途 | Endpoint |
|---|---|
| login | `POST /v1/login` |
| overview | `GET /v1/debugmode/information` |
| ports | `GET /v2/network/ports_status` |
| WAN | `GET /v2/network/wan/status` |
| clients | `GET /v2/clients` |
| events | `GET /v2/eventlogs?limit=50` |
| logout | `POST /v1/logout` |

Login body 使用 `force=false`。成功後以 `Authorization: Bearer <token>` 查詢；不論成功或失敗都嘗試 logout。若回應表示已有 session 且未提供 token，不再查詢其他 endpoint。

## Redaction

Debug bundle 必須遮蔽：password、SID、Bearer token、NAS hostname、serial、LAN/WAN/Tailnet address、MAC、DNS server 與 client identity。一般 API 可依使用者權限顯示必要的區網資訊，但不得記錄 secrets。

# 2026-09-16 deployed status page

This directory reconstructs the artifact that was actually deployed before the standalone Go dashboard was proposed: an Uptime Kuma status page named **私人網路狀態**, grouped into 網路, NAS and 服務, plus a **詳細** menu link to `/status/home-network`.

The original cached scripts contained private addresses and credentials. They are intentionally not preserved here. Copy `.env.example` to a secret location, export its values, install `requirements.txt`, then run `python configure.py`. Review the script against the installed Kuma version first: Socket.IO events are not a stable public API.

`patch-detail-link.ps1` reproduces the final bundle patch. It is historical evidence, not the recommended deployment path: it is build-specific and will be overwritten by Kuma upgrades. Prefer a bookmark or reverse-proxy navigation link.

Open [`preview/index.html`](preview/index.html) directly to view a dependency-free reconstruction. It contains sample states and no live credentials or API calls.

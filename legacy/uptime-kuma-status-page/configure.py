"""Rebuild the 2026-09-16 private Uptime Kuma status page.

Credentials and device addresses are supplied only through environment
variables. The script is idempotent for monitors matched by name.
"""
import copy
import os
import threading

import socketio


def required(name):
    value = os.environ.get(name, "").strip()
    if not value or value == "replace-me":
        raise RuntimeError("missing environment variable: " + name)
    return value


BASE = {"type": "http", "name": "", "url": "https://", "interval": 60,
        "retryInterval": 30, "maxretries": 2, "timeout": 10,
        "accepted_statuscodes": ["200-399"], "notificationIDList": {},
        "active": True, "maxredirects": 10, "saveResponse": False}


def main():
    url, username, password = required("UK_URL"), required("UK_USERNAME"), required("UK_PASSWORD")
    slug = os.environ.get("STATUS_SLUG", "home-network")
    specs = [
        {"name": "QHora Ping", "type": "ping", "hostname": required("QHORA_HOST"), "url": ""},
        {"name": "QuRouter Web", "type": "http", "url": required("QUROUTER_URL")},
        {"name": "QTS", "type": "http", "url": required("QTS_URL")},
        {"name": "AdGuard DNS", "type": "port", "hostname": required("ADGUARD_HOST"), "port": 53, "url": ""},
        {"name": "AdGuard Web", "type": "http", "url": required("ADGUARD_URL")},
    ]
    sio, monitors, pages, loaded = socketio.Client(reconnection=False), {}, {}, threading.Event()

    @sio.on("monitorList")
    def monitor_list(data):
        monitors.update(data or {}); loaded.set()

    @sio.on("statusPageList")
    def status_pages(data):
        pages.update(data or {})

    def call(event, *args):
        payload = args[0] if len(args) == 1 else tuple(args)
        result = sio.call(event, payload, timeout=20)
        if not result or not result.get("ok"):
            raise RuntimeError("{} failed: {}".format(event, result))
        return result

    sio.connect(url, transports=["websocket"])
    call("login", {"username": username, "password": password, "token": ""})
    loaded.wait(10)
    ids = {m.get("name"): int(mid) for mid, m in monitors.items()}
    for spec in specs:
        if spec["name"] not in ids:
            monitor = copy.deepcopy(BASE); monitor.update(spec)
            ids[spec["name"]] = int(call("add", monitor)["monitorID"])
    if slug not in pages:
        call("addStatusPage", "私人網路狀態", slug)
    page = call("getStatusPage", slug)["config"]
    page.update({"slug": slug, "title": "私人網路狀態",
                 "description": "QHora、QNAP NAS 與自架服務即時狀態",
                 "autoRefreshInterval": 60, "theme": "auto", "showTags": False,
                 "footerText": "僅限私人網路存取", "showPoweredBy": True})
    groups = [
        {"name": "網路", "monitorList": [{"id": ids["QHora Ping"], "sendUrl": False}, {"id": ids["QuRouter Web"], "sendUrl": True}]},
        {"name": "NAS", "monitorList": [{"id": ids["QTS"], "sendUrl": True}]},
        {"name": "服務", "monitorList": [{"id": ids["AdGuard DNS"], "sendUrl": False}, {"id": ids["AdGuard Web"], "sendUrl": True}]},
    ]
    call("saveStatusPage", slug, page, page.get("logo", ""), groups)
    sio.disconnect()
    print(url.rstrip("/") + "/status/" + slug)


if __name__ == "__main__":
    main()

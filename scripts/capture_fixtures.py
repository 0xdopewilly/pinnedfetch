"""Capture real MCP `initialize` + `tools/list` responses as test fixtures.

Each fixture stores the raw HTTP bodies exactly as a GenLayer validator would
receive them (Streamable HTTP servers answer with JSON or SSE-framed JSON-RPC),
so direct-mode tests exercise the same parsing path as production.

Usage: .venv/bin/python scripts/capture_fixtures.py
"""

import json
import pathlib
import urllib.request

PROTO = "2025-06-18"
SERVERS = {
    "deepwiki": "https://mcp.deepwiki.com/mcp",
    "cloudflare_docs": "https://docs.mcp.cloudflare.com/mcp",
    "gitmcp_python_sdk": "https://gitmcp.io/modelcontextprotocol/python-sdk",
    "internetcourt": "https://mcp.internetcourt.org/mcp",
}
OUT = pathlib.Path(__file__).resolve().parent.parent / "tests" / "fixtures"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
    "User-Agent": "toolbond/0.1",
    "MCP-Protocol-Version": PROTO,
}


def post(url: str, payload: dict, headers: dict) -> tuple[int, dict, str]:
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.status, {k.lower(): v for k, v in resp.headers.items()}, resp.read().decode("utf-8", "replace")


def capture(name: str, url: str) -> None:
    init_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {"protocolVersion": PROTO, "capabilities": {}, "clientInfo": {"name": "toolbond", "version": "0.1"}},
    }
    status, headers, init_body = post(url, init_payload, HEADERS)
    session_headers = dict(HEADERS)
    if "mcp-session-id" in headers:
        session_headers["Mcp-Session-Id"] = headers["mcp-session-id"]
    list_status, _, list_body = post(url, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}, session_headers)
    fixture = {
        "url": url,
        "initialize": {"status": status, "session_id": headers.get("mcp-session-id", ""), "body": init_body},
        "tools_list": {"status": list_status, "body": list_body},
    }
    (OUT / f"{name}.json").write_text(json.dumps(fixture, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{name}: init {status} ({len(init_body)} B), tools/list {list_status} ({len(list_body)} B)")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for server_name, server_url in SERVERS.items():
        try:
            capture(server_name, server_url)
        except Exception as exc:  # a dead server must not block the others
            print(f"{server_name}: FAILED {exc!r}")

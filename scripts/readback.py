"""Contract readbacks for PinnedFetch v2, read with gen_call (standard library only).

    python3 scripts/readback.py > docs/evidence/readbacks.md
"""

import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lib"))

import genlayer_read  # noqa: E402

RPC = "https://studio-dev.genlayer.com/api"
CONTRACT = "0xf9f6FD0E66f79471EAd67feA82fff1c3723Ce5f2"


def view(method: str, *args):
    for attempt in range(4):
        time.sleep(2.5 * attempt + 0.8)  # Studio Next rate-limits gen_call
        try:
            raw = genlayer_read.read_view(RPC, CONTRACT, method, list(args))
            return json.loads(raw) if isinstance(raw, str) and raw[:1] in "{[" else raw
        except genlayer_read.ReadError:
            if attempt == 3:
                raise


def main() -> int:
    stats = view("get_stats")
    listed = view("list_pins", 0, 20)
    items = listed.get("items", listed) if isinstance(listed, dict) else listed
    out = [
        "# Contract readbacks (PinnedFetch v2)",
        "",
        f"Read {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())} with `gen_call` from `{CONTRACT}` through `{RPC}`.",
        "",
        "## get_stats",
        "",
        "```json",
        json.dumps(stats, indent=1, sort_keys=True),
        "```",
        "",
        "## Pins",
        "",
        "| URL | Version | Root | Tools | Last drift check |",
        "|---|---|---|---|---|",
    ]
    checks = []
    for item in items:
        url = item["url"]
        pin = view("get_pin", url)
        last = view("get_last_check", url)
        tools = pin.get("tools") or {}
        drift = last.get("drift", "none") if isinstance(last, dict) and last.get("found", True) else "none"
        out.append(f"| `{url}` | {pin.get('version')} | `{str(pin.get('root', ''))[:16]}…` | {len(tools)} | {drift} |")
        if tools:
            name, entry = sorted(tools.items())[0]
            tool_hash = entry if isinstance(entry, str) else entry.get("hash")
            ok = view("verify_tool_at", url, int(pin.get("version", 1)), name, tool_hash)
            bad = view("verify_tool_at", url, int(pin.get("version", 1)), name, "0" * 64)
            checks.append(f"| `{url}` | `{name}` | `{tool_hash[:16]}…` | {str(ok).lower()} | {str(bad).lower()} |")
    out += ["", "## verify_tool_at", "", "The pinned hash verifies; a wrong hash does not.", "",
            "| URL | Tool | Pinned hash | verify_tool_at(pinned) | verify_tool_at(zeros) |", "|---|---|---|---|---|"] + checks
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())

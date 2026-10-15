"""Decode every logged transaction from the chain into a Markdown table.

Takes every transaction hash listed in docs/DEPLOYMENTS.md, fetches
each with eth_getTransactionByHash, and prints contract, method, short arguments, status,
execution result, validator votes and any error, all decoded from the chain itself. For a
deployment it prints the SHA-256 of the contract code stored in the deploy transaction. pin and check
return nothing; their results are read back from contract state by scripts/readback.py.

    python3 scripts/tx_table.py > docs/evidence/transactions.md
"""

import base64
import hashlib
import json
import pathlib
import sys
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lib"))

from genlayer_read import decode  # noqa: E402

RPC = "https://studio-dev.genlayer.com/api"
EXPLORER = "https://explorer-studio-dev.genlayer.com"
NAMES = {
    "0xf9f6fd0e66f79471ead67fea82fff1c3723ce5f2": "PinnedFetch v2",
    "0x8d4b7b2376069251e05f3aef7c3f1f433c2f040c": "PinnedFetch v1",
}


def rpc(method: str, params: list):
    request = urllib.request.Request(RPC, data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode(),
                                     headers={"Content-Type": "application/json", "User-Agent": "pinnedfetch-evidence"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read())["result"]


def framed(b64: str):
    raw = base64.b64decode(b64 or "")
    if not raw:
        return None, None
    if raw[0] == 0:
        try:
            value = decode(raw[1:])
            return (json.loads(value) if isinstance(value, str) and value[:1] in "{[" else value), None
        except Exception:
            return None, None
    return None, raw[1:].decode("utf-8", "replace")


def short(value, limit=80) -> str:
    text = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
    text = text.replace("|", "/").replace("\n", " ")
    return text if len(text) <= limit else text[: limit - 1] + "…"


def main() -> int:
    import re

    hashes = []
    for h in re.findall(r"0x[0-9a-f]{64}", (ROOT / "docs/DEPLOYMENTS.md").read_text()):
        if h not in hashes:
            hashes.append(h)
    rows = []
    for h in hashes:
        tx = rpc("eth_getTransactionByHash", [h])
        time.sleep(0.3)
        data = tx.get("consensus_data") or {}
        leader = data.get("leader_receipt")
        leader = leader[0] if isinstance(leader, list) and leader else (leader or {})
        _, error = framed(leader.get("result", ""))
        calldata = tx.get("data", {}).get("calldata") if isinstance(tx.get("data"), dict) else None
        message = decode(base64.b64decode(calldata)) if calldata else {}
        method = message.get("", "(deploy)") if isinstance(message, dict) else "(deploy)"
        to = str(tx.get("to_address") or "").lower()
        contract = NAMES.get(to, "deploy" if method == "(deploy)" else to[:10])
        args = message.get("args", []) if isinstance(message, dict) else []
        code = tx.get("data", {}).get("contract_code") if isinstance(tx.get("data"), dict) else None
        if method == "(deploy)" and code:
            args = [f"source SHA-256 {hashlib.sha256(base64.b64decode(code)).hexdigest()}"]
        outcome = short(error, 80) if error else ""
        votes = list((data.get("votes") or {}).values())
        rows.append((str(tx.get("created_at", ""))[:19].replace("T", " "), contract, method, ", ".join(short(a) for a in args), tx.get("status"),
                     tx.get("txExecutionResultName"), outcome, f"{votes.count('agree')} agree, {votes.count('disagree')} disagree", h))
    print("| Created (UTC) | Contract | Call | Arguments | Status | Votes | Transaction |")
    print("|---|---|---|---|---|---|---|")
    for t, contract, method, args, status, execution, outcome, votes, h in rows:
        status_text = status + ("" if execution == "FINISHED_WITH_RETURN" else ", " + str(execution)) + (f": {outcome}" if outcome else "")
        print(f"| {t} | {contract} | `{method}` | {args} | {status_text} | {votes} | [{h[:10]}…]({EXPLORER}/tx/{h}) |")
    return 0


if __name__ == "__main__":
    sys.exit(main())

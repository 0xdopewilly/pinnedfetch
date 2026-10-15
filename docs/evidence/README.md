# Evidence for PinnedFetch

Everything here can be checked against the chain without trusting this repository. The scripts
use only the Python standard library.

| File | What it is | How to verify it |
|---|---|---|
| `transactions.md` | all 11 transactions in [../DEPLOYMENTS.md](../DEPLOYMENTS.md) (both deployments, every `pin` and `check`), decoded from `eth_getTransactionByHash`: method, arguments, status, validator votes | `python3 scripts/tx_table.py > /tmp/t.md` and compare |
| `readbacks.md` | contract view outputs read with `gen_call` from v2: `get_stats`, `get_pin` for each pinned server, `get_last_check`, and `verify_tool_at` with the pinned hash and with a wrong one | `python3 scripts/readback.py` (same reads, current state) |

## Deployed source

Each deploy transaction stores the contract code it deployed. `transactions.md` prints the SHA-256
of that stored code, so the match below comes from the chain, not from this repo.

| Version | Address | SHA-256 of the code in the deploy transaction | Same bytes as |
|---|---|---|---|
| v2 (live) | `0xf9f6FD0E66f79471EAd67feA82fff1c3723Ce5f2` | `b5b3daacfc272fbb09d5845e96613b24f6285dc4bf4404070d866a7e2f03ad32` | `contracts/pinned_fetch.py` at commit `f51d11c` |
| v1 | `0x8D4B7B2376069251E05f3aef7C3f1F433c2F040c` | `440bafc7a086d898c71cf1b422cbb0bb6152fe24ae835e1f542129acecadd1a8` | `contracts/pinned_fetch.py` at commit `5c5f8fd` |

```bash
git show f51d11c:contracts/pinned_fetch.py | sha256sum
git show 5c5f8fd:contracts/pinned_fetch.py | sha256sum
```

`contracts/pinned_fetch.py` is generated from `contracts/src/pinned_fetch.py` by
`scripts/bundle.py`, which inlines `lib/gl_mcp.py`; `python3 scripts/bundle.py --check` confirms
the two are in step.

## What the evidence shows

- All 11 transactions are FINALIZED, each with 3 validators agreeing and none disagreeing. In a
  `pin`, each voting validator ran the MCP handshake itself and derived the same manifest root
  (the other 2 of 5 stay idle once quorum is reached).
- The v2 `check` on DeepWiki returned `MATCH`: validators re-fetched the server and got the
  pinned root back. Its stored record is in `readbacks.md`.
- `verify_tool_at` returns true for the pinned tool hash and false for a wrong one, so an agent
  can ask the contract whether the tool text it was given is the pinned one.

All transactions were signed by the maintainer's testnet account
`0xE258D2604AEC1321ddD58f179001cc6A8c442930`.

## Limits of the network

- Studio Next is a hosted preview network and can be reset; if that happens, these hashes stop
  resolving and the contract needs redeploying (`scripts/glw deploy contracts/pinned_fetch.py`).
- Studio Next limits `gen_call` to 20 reads per 10 seconds per contract and about 500 RPC requests
  an hour per client. The scripts pace their reads and retry.
- A contract read is only as honest as the RPC node that answers it. These reads used the public
  Studio Next endpoint, `https://studio-dev.genlayer.com/api`.

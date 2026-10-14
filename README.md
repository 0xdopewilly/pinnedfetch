# PinnedFetch

A GenLayer Intelligent Contract that makes the exact bytes of a remote MCP server's tools a consensus fact,
and later records, by consensus, whether those bytes have changed.

MCP tool descriptions are instructions that AI agents follow. A server can change them after a user approved
it, and the client rarely notices. PinnedFetch lets any contract or off-chain client rely on what a server
said at a point in time, verified by validators who each fetched it themselves.

## Live on GenLayer Studio Next (chain 61997)

| | |
|---|---|
| Contract (v2) | [`0xf9f6FD0E66f79471EAd67feA82fff1c3723Ce5f2`](https://explorer-studio-dev.genlayer.com/address/0xf9f6FD0E66f79471EAd67feA82fff1c3723Ce5f2) |
| Deployed source | `contracts/pinned_fetch.py`, SHA-256 `b5b3daacfc272fbb09d5845e96613b24f6285dc4bf4404070d866a7e2f03ad32` |
| Pinned by consensus | DeepWiki and Internet Court on v2 (3 validators agreeing each); four servers on v1 |
| Drift checks | DeepWiki `MATCH` on v2; DeepWiki and Internet Court `MATCH` on v1 |
| Version 1 | [`0x8D4B7B2376069251E05f3aef7C3f1F433c2F040c`](https://explorer-studio-dev.genlayer.com/address/0x8D4B7B2376069251E05f3aef7C3f1F433c2F040c), before the audit fixes below |

Every transaction hash is in [docs/DEPLOYMENTS.md](docs/DEPLOYMENTS.md).

## Interface

| Method | Kind | What it does |
|---|---|---|
| `pin(url)` | write | Pins the live manifest of `url` as a new version |
| `check(url)` | write | Re-fetches `url` and records how it compares with its latest pin |
| `get_pin(url)` | view | Latest pin: root, per-tool hashes, protocol, pinner, last drift check |
| `get_pin_version(url, version)` | view | One version in full, including the canonical text of every tool |
| `get_last_check(url)` | view | Latest drift check, including the verified text of changed tools |
| `verify_tool_at(url, version, name, hash)` | view | `true` when `hash` is tool `name` in pin `version`: use it for the version you approved |
| `verify_tool(url, name, hash)` | view | the same against the latest pin (anyone can pin a newer version) |
| `get_last_drift(url)` | view | the latest check that found a change, kept even when later checks fail |
| `list_pins(offset, limit)`, `get_stats()` | view | Registry listing and counters |

Views return JSON strings. Off-chain clients read them with genlayer-js `readContract`; other contracts call
them with a contract-to-contract view call.

## How consensus is used

Both writes use custom leader and validator functions (`gl.vm.run_nondet`).

**`pin`.** The leader runs the MCP handshake (`initialize`, then `tools/list`), canonicalizes every tool with
[TBCM-1](docs/TBCM-1.md) and hashes it. Each validator repeats the whole fetch itself and accepts only if its
digest equals the leader's: same root, same per-tool hashes, same canonical text. If the leader failed,
validators accept only the same classified failure. What gets stored is exactly what every validator saw.

**`check`.** Validators re-fetch and agree on one drift class:

| Class | Meaning | How validators accept it |
|---|---|---|
| `MATCH` | the live manifest has the pinned root | their own observation is identical |
| `DIFFERS` | the manifest changed | their own observation is identical, so the stored changed tools are verified content, not the leader's word |
| `UNSTABLE` | the server returned two different manifests in a row | they see `UNSTABLE` themselves |
| `UNREACHABLE` | the server could not be read | accepted from any leader: it changes no pin and never counts as a pass |

## Version 2

An independent audit of the ToolBond codebase found issues that also touched this primitive. v2 fixes them:

- TBCM-1 drops only a tool's own top-level `_meta`; a nested `_meta` key is data and changes the hash.
- Validators accept `UNSTABLE` only when they observe it themselves.
- `verify_tool_at` checks a specific version, and `get_last_drift` keeps the last real change.
- SSE lines split only on CR, LF and CRLF; unpaired surrogates are a classified error.
- URL hosts reject `#`, `?`, backslashes, IP literals and private suffixes.

## Built on gl_mcp

[`lib/gl_mcp.py`](lib/gl_mcp.py) is a dependency-free MCP client sized for GenVM non-deterministic blocks
([guide](docs/gl_mcp.md)). It handles the `initialize` handshake, the `Mcp-Session-Id` header, JSON, SSE and
batch responses, and bounded pagination (3 pages, 24 tools, 64 KB). Its errors carry stable prefixes
(`[EXTERNAL]`, `[TRANSIENT]`), so validators can agree on a failure as well as on a success. Any contract can
inline it: put `# @@include gl_mcp` in a source under `contracts/src/` and run `python3 scripts/bundle.py`,
which refuses to build when two inlined modules define the same top-level name.

## Run it

Needs [uv](https://docs.astral.sh/uv/) and Node 20+.

```bash
./scripts/setup.sh                                        # Python 3.12 venv, GenLayer test tools, CLI
GENVM_VERSION=v0.6.0-rc5 .venv/bin/python -m pytest -q    # 37 tests: direct-mode contract, gl_mcp, vectors
python3 scripts/bundle.py --check                         # generated contract is up to date
scripts/glw deploy contracts/pinned_fetch.py              # deploy to Studio Next (keystore in .env.local)
```

Direct-mode tests (`tests/direct/test_pinned_fetch.py`) cover pinning, versioning, each drift class,
`verify_tool`, unsafe URLs, HTTP errors and unreadable manifests. `tests/vectors/tbcm1.json` holds 29 TBCM-1
vectors for other implementations to check against.

## Layout

| Path | What |
|---|---|
| `contracts/src/pinned_fetch.py` | contract source |
| `contracts/pinned_fetch.py` | deployable single file, generated by `scripts/bundle.py` |
| `lib/gl_mcp.py` | MCP client and TBCM-1 hashing |
| `docs/TBCM-1.md`, `docs/gl_mcp.md` | canonical form spec, client guide |
| `tests/` | direct-mode tests, fixtures captured from real servers, TBCM-1 vectors |

## Origin

PinnedFetch was built as the base layer of [ToolBond](https://github.com/0xdopewilly/toolbond), a bonded
registry where publishers stake GEN behind their tools and validators judge them. This repository holds the
primitive on its own, with the commit history of its files.

## License

MIT

# Contract readbacks (PinnedFetch v2)

Read 2026-10-15 20:29:57 UTC with `gen_call` from `0xf9f6FD0E66f79471EAd67feA82fff1c3723Ce5f2` through `https://studio-dev.genlayer.com/api`.

## get_stats

```json
{
 "checks": 1,
 "drifts": 0,
 "pins": 2,
 "servers": 2
}
```

## Pins

| URL | Version | Root | Tools | Last drift check |
|---|---|---|---|---|
| `https://mcp.deepwiki.com/mcp` | 1 | `923f63c630de89d0…` | 3 | MATCH |
| `https://mcp.internetcourt.org/mcp` | 1 | `07c7b0e1876e6597…` | 3 | none |

## verify_tool_at

The pinned hash verifies; a wrong hash does not.

| URL | Tool | Pinned hash | verify_tool_at(pinned) | verify_tool_at(zeros) |
|---|---|---|---|---|
| `https://mcp.deepwiki.com/mcp` | `ask_wiki_question` | `217e49111cb69fbf…` | true | false |
| `https://mcp.internetcourt.org/mcp` | `consult_internet_court` | `9839285f7fce8fac…` | true | false |

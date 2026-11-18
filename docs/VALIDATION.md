# Validation status

Implemented on 2026-11-18. SDK target: GenVM v0.2.16 with the pinned `py-genlayer` dependency in the contract header.

Checks performed:

- Behavioral tests with deterministic GitHub/AI/message fixtures: reward authorization, finality callback permissions, owner/developer restrictions, immutable terms/submission, duplicate settlement prevention, criterion aggregation, malformed model output, evidence integrity, bounded retries and exact expiry boundaries.
- Real GenVM SDK validation and ABI extraction using `genvm-linter==0.11.0`.
- Pyright checking using the SDK configured by the same linter.

The behavior harness uses ordinary Python with a minimal fake `genlayer` module. It is explicitly not evidence of real validator agreement, GenVM resource consumption, live GitHub/LLM access, EVM message delivery or successful GEN settlement.

## Live Studio deployment

On 2026-11-18, the unchanged contract source was uploaded to Studio Next v0.123.0-rc.13 and deployed in Normal (Full Consensus) mode using its built-in account. No external wallet connection was needed.

- Contract: [0xD3f16151B5c711B7C3Ef14c9b043A81419c32791](https://explorer-studio-next.genlayer.com/address/0xD3f16151B5c711B7C3Ef14c9b043A81419c32791)
- Transaction: [0x735162f2689a7fa927d3c70c6dbdf1f053c5435da1f5d59fe87e45f253299beb](https://explorer-studio-next.genlayer.com/tx/0x735162f2689a7fa927d3c70c6dbdf1f053c5435da1f5d59fe87e45f253299beb)
- Explorer showed FINALIZED, GenVM SUCCESS and consensus Accepted.
- A live `get_bounty()` read returned state DRAFT and owner `0x6a396e113A1fDFDde23e6908550A48D0B3FcbeB0`.
- Source SHA-256: `eb679732252b8d333677b20cd6daa52d6757d1334c833a2cf798838e46af8632`.

This verifies constructor deployment and a live storage read in the Studio development sandbox. It does not verify a funded bounty, live AI evaluation, finality self-message settlement, appeals or an external GEN payout. Those end-to-end checks remain outstanding. Studio preview state may reset.

# Validation status

Implemented on 2026-11-18. SDK target: GenVM v0.2.16 with the pinned `py-genlayer` dependency in the contract header.

Checks performed:

- Behavioral tests with deterministic GitHub/AI/message fixtures: reward authorization, finality callback permissions, owner/developer restrictions, immutable terms/submission, duplicate settlement prevention, criterion aggregation, malformed model output, evidence integrity, bounded retries and exact expiry boundaries.
- Real GenVM SDK validation and ABI extraction using `genvm-linter==0.11.0`.
- Pyright checking using the SDK configured by the same linter.

The behavior harness uses ordinary Python with a minimal fake `genlayer` module. It is explicitly not evidence of real validator agreement, GenVM resource consumption, live GitHub/LLM access, EVM message delivery or successful GEN settlement.

No deployed contract address or live payout is claimed. A funded GenLayer signing account and network are required for deployment and end-to-end settlement validation. Release candidates should exercise the README flow on testnet with small test-GEN amounts, including protocol appeals and external transfer receipts.

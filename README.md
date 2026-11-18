# BountyProof

**AI-verified GitHub bounty settlement on GenLayer.** Lock a task and GEN reward, submit an exact GitHub commit, and let independent validators assess each acceptance criterion before authorizing payment.

One contract = one bounty, one designated developer, one immutable submission, one reward. This keeps the MVP small and prevents submission-slot squatting and reward splitting.

## Deployed contract

Deployed using GenLayer Studio's built-in account on **Studio Next / Studio Dev** (development sandbox) on 2026-11-18.

- [Contract Explorer](https://explorer-studio-next.genlayer.com/address/0xD3f16151B5c711B7C3Ef14c9b043A81419c32791)
- Address: `0xD3f16151B5c711B7C3Ef14c9b043A81419c32791`
- [Deployment transaction](https://explorer-studio-next.genlayer.com/tx/0x735162f2689a7fa927d3c70c6dbdf1f053c5435da1f5d59fe87e45f253299beb): **FINALIZED**, GenVM **SUCCESS**, consensus **Accepted**.
- `get_bounty()` returned `DRAFT` and the built-in account as owner. No bounty reward has been funded; no live settlement is claimed.
- The deployed source matches commit `7554ae6c79b1b135f71027a0839500c04b1f2ce0`. See [deployment metadata](deployments/studio-next.json).

Studio preview state may reset. This deployment provides sandbox evidence, not a persistent public-testnet deployment or an audit.

## What is implemented

- Payable escrow creation with immutable requirements, 3–5 criteria, repository, base commit, workflow, developer and deadlines.
- Developer-only submission of a PR number, full head SHA, Actions run ID and SHA-256 evidence commitment.
- Independent GitHub retrieval and semantic assessment by leader and validators, with agreement on criterion statuses, verdict and evidence digest.
- Before/after source and patches bound to full commits. Successful CI is supporting evidence; no submitted code is executed.
- `ACCEPTED`, `REJECTED`, `INCONCLUSIVE` reports with criterion reasons and changed-file references.
- A finalized self-message authorizes the verdict. Reward and refund transfers execute on finalization.
- One-time reward/refund, protected pending evaluations, bounded inconclusive retries and predetermined expiry rules.

## Quick start

Python 3.12+ for development tools. Contract runs in GenVM, not ordinary CPython.

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
genvm-lint check contracts/bounty_proof.py
genvm-lint typecheck contracts/bounty_proof.py
```

`tests/` uses mocked GitHub, AI and message delivery. It verifies contract behavior but does not emulate consensus, EVM transfer execution or protocol finality. `genvm-lint check` separately validates the contract against the real SDK. The runner is pinned to the `py-genlayer` hash bundled with GenVM v0.2.16.

## Deploy and use

1. Open [GenLayer Studio](https://studio.genlayer.com/) or [Studio Next](https://studio-next.genlayer.com/). Load `contracts/bounty_proof.py` and deploy with **no constructor arguments**, using the bounty owner's wallet. For a configured GenLayer CLI account/network, the equivalent deployment command is `genlayer deploy --contract contracts/bounty_proof.py`.
2. Call `create_bounty()` as the deployer. Attach the reward as transaction value: **10 GEN = 10000000000000000000 wei**. Use ordinary EOA wallets for owner/developer. See [the parameter guide](docs/USAGE.md).
3. Implement the change in a public repository, open a PR, and complete the locked GitHub Actions workflow at that exact PR head. Do not push more commits or rerun CI after submitting.
4. Generate verified submission arguments:

   ```bash
   python tools/prepare_evidence.py OWNER/REPO PR_NUMBER ACTIONS_RUN_ID
   ```

   Call `submit_solution()` with the printed `args`, using the designated developer wallet.
5. Anyone may call `evaluate_solution()` before the review deadline. Read `get_verdict()`. It initially reports `EVALUATING`; wait for the evaluation transaction to finalize and the internal `finalize_verdict` message to run.
6. When the state is `ACCEPTED`, the developer calls `claim_reward()`. `PAYOUT_QUEUED` means a finalized external transfer was requested; verify the chain receipt and recipient balance before treating it as received.
7. `INCONCLUSIVE` may be evaluated again, up to three attempts total. An unsubmitted bounty is refundable at the submission deadline; a submitted, rejected or inconclusive bounty is refundable at the review deadline. Anyone can trigger `resolve_expiry()`; funds always go to the owner.

There is no owner override or custom application arbitrator. Disputes use GenLayer's protocol appeals before finality. After finalization, an accepted verdict cannot be refunded and a rejected verdict cannot be retried. The developer should submit early enough to allow evaluation before the review deadline.

## Methods

| Method | Caller | Effect |
| --- | --- | --- |
| `create_bounty(...)` | Deployer | Lock terms and attached GEN once |
| `submit_solution(pr_number, commit, run_id, evidence_hash)` | Designated developer | Lock one submission before deadline |
| `evaluate_solution()` | Anyone | Independently assess evidence; max 3 attempts |
| `finalize_verdict(attempt)` | Contract itself | Apply verdict after parent evaluation finality |
| `claim_reward()` | Developer | Queue reward for a finalized accepted verdict |
| `resolve_expiry()` | Anyone | Queue owner refund under locked expiry rules |
| `get_bounty()` | Anyone | Read terms, commitments and submission |
| `get_verdict()` | Anyone | Read state and criterion report |

## MVP boundaries

Public repositories only; 1–10 changed text files, at most 16,000 UTF-8 bytes per before/after file, and a 100,000-character total evidence budget. The base must be an ancestor of the submitted head. Changed workflow files, binary/missing patches, missing source, moved PR heads, changed CI evidence, failed CI, oversized evidence and malformed model responses produce `INCONCLUSIVE`.

The locked CI run must belong to the bounty repository, reference the exact head, use the locked workflow path and be a successful `push` or `pull_request` run. Fork-only workflows and synthetic merge-SHA test runs are outside this MVP. Criteria that need unseen unchanged files or actual runtime behavior should remain `UNKNOWN` rather than receive a guessed approval.

GitHub availability, rate limits, AI judgment and validator consensus remain dependencies. Prompt injection defenses reduce risk but cannot prove model correctness. This is a testnet MVP, not an audited escrow. See [security and settlement details](docs/SECURITY.md) and [validation status](docs/VALIDATION.md).

## References

- [GenLayer value transfers](https://docs.genlayer.com/developers/intelligent-contracts/features/value-transfers)
- [GenLayer messages and finality](https://docs.genlayer.com/developers/intelligent-contracts/features/messages)
- [Non-deterministic execution](https://docs.genlayer.com/developers/intelligent-contracts/features/non-determinism)
- [GenVM linter](https://docs.genlayer.com/api-references/genlayer-linter)

MIT licensed.

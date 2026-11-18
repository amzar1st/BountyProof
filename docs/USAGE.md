# Parameter guide

## Creation

The deployer calls `create_bounty`, with reward attached as transaction value:

| Parameter | Example / rule |
| --- | --- |
| `repository` | `amzar1st/your-public-project`; exact GitHub canonical casing |
| `base_commit` | Full lowercase 40-character SHA of the agreed starting commit |
| `developer` | Designated developer's GenLayer EOA address, different from owner |
| `requirements` | `Fix the login crash without changing existing authentication behavior.` |
| `criteria` | JSON array of 3–5 distinct, specific acceptance criteria |
| `workflow` | `.github/workflows/test.yml`; pre-existing trusted workflow |
| `deadline` | Future Unix timestamp in seconds, no more than 90 days away |
| `review_deadline` | Unix seconds, between 1 hour and 14 days after `deadline` |
| Transaction value | Integer GEN wei; 1 GEN is 10^18 wei |

Suggested criteria for a small authentication fix:

```json
[
  "An empty login payload returns the existing validation error rather than raising an exception.",
  "Regression tests cover both empty payload and successful login using the existing test framework.",
  "The successful login response schema, cookie options and authentication method signatures remain unchanged."
]
```

Choose criteria whose evidence fits the MVP context. Do not describe a whole application's behavior when only a small patch can be retrieved.

To calculate deadlines locally:

```bash
python -c 'import time; n=int(time.time()); print({"deadline":n+86400,"review_deadline":n+259200})'
```

## Evidence commitments

All hashes use lowercase SHA-256 hex of UTF-8 canonical JSON:

```python
json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
```

`terms_hash` commits to all immutable creation inputs and the funded reward amount. `evidence_hash` commits to normalized GitHub Actions run metadata, not developer-written test claims. It includes `id`, `head_sha`, `status`, `conclusion`, `path`, `event`, `run_attempt`, `html_url`, and repository names. `tools/prepare_evidence.py` calculates it from GitHub. Rerunning CI changes `run_attempt`, invalidating the commitment.

`submission_hash` binds the terms hash, head commit, PR, run ID and evidence hash. The final report also records `evidence_digest`, a hash of the actual fetched source, patches, base/head and normalized CI metadata. Validators must reproduce that digest independently.

Only GitHub API and raw GitHub URLs derived by the contract are fetched. No user-supplied arbitrary URLs, CI logs or PR descriptions are trusted as instructions.

## State and timing

- `DRAFT`: only deployer may create and fund once.
- `OPEN`: only designated developer may submit while `now < deadline`.
- `SUBMITTED` / `INCONCLUSIVE`: anyone may evaluate while `now < review_deadline`, at most three attempts.
- `EVALUATING`: waiting for finalized self-message. Evaluation, claim and refund are blocked.
- `ACCEPTED`: only developer may queue a reward. No application expiry of an approved reward.
- `REJECTED`: owner refund is available at review deadline.
- `PAYOUT_QUEUED` / `REFUND_QUEUED`: terminal, preventing repeated emissions.

Expiry uses `now >= deadline` or `now >= review_deadline`; there is no boundary overlap with submissions/evaluations. GEN transfers execute asynchronously after their requesting transaction finalizes. Queue state is not a delivery receipt.

The contract uses GenVM's transaction datetime. It never trusts a user-provided current time. A timestamp delay is not used as a substitute for consensus finality.

# Security and settlement assumptions

## Escrow invariants

The deployer can fund exactly one bounty with positive transaction value. Terms cannot be edited, funds cannot be topped up through public methods, and nobody can redirect reward or refund recipients. The preselected developer prevents a stranger from occupying the only submission slot. Ownership of a GitHub account is not inferred; the owner selects the payment address before funding.

Evaluation runs with copied immutable inputs. It performs no storage writes or message emission inside nondeterministic execution. Validators independently fetch and assess evidence, and must agree on aggregate verdict, criterion statuses and the evidence digest. Reason wording is not compared. Model output cannot directly choose the aggregate verdict: any `FAIL` yields `REJECTED`, otherwise any `UNKNOWN` yields `INCONCLUSIVE`, and all `PASS` yields `ACCEPTED`.

After evaluation, the contract enters `EVALUATING` and emits a self-call on parent finalization. Only the contract address may finalize the stored verdict, and the callback must match the attempt number and pending state. Claiming requires the resulting `ACCEPTED` state. Refunds cannot consume funds belonging to accepted or pending evaluations. Terminal queue states prevent repeated transfer emissions.

## Evidence limits

The locked text and criteria are the original task; mutable GitHub issue/PR descriptions cannot replace them. Full commit hashes bind before/after source and comparison. CI metadata is checked against the locked run hash, exact commit, repository and workflow. Workflow changes require manual review and therefore return `INCONCLUSIVE`.

CI may be compromised or misleading even when the workflow file is unchanged (for example, modified test scripts). The model must inspect code and tests, and may not approve solely from a green CI run. BountyProof does not execute arbitrary code or cryptographically prove software correctness. It does not prove PR authorship, enforce merge, inspect an entire repository, or establish hidden runtime behavior. Unavailable evidence is not rejection on the merits.

Source files, comments and requirements can contain malicious instructions. The prompt treats all supplied content as untrusted data; schema checks require every criterion and real changed-file references for passing rows. These controls cannot eliminate AI mistakes or coordinated validator compromise. Consensus disagreement may fail/revert the evaluation transaction; it is not the same as a stored `INCONCLUSIVE` verdict.

## Liveness and funds

Once an evaluation is pending, a finalized self-call must execute before settlement can proceed. If protocol finalization or internal message delivery stalls, funds remain held. There is deliberately no timestamp-based bypass that could refund an eventual accepted evaluation.

An unsubmitted bounty expires at its submission deadline. Submitted/rejected/inconclusive bounties expire at the review deadline unless evaluation is already pending. No evaluator is forced to act: submission alone does not earn a reward. Anyone may pay evaluation costs; the developer should allow time to initiate it before the cutoff. Retries are limited to three attempts and only an inconclusive verdict permits another attempt.

Owner and developer should be EOAs on the GenLayer Chain. This MVP does not detect recipient account type. A recipient contract can reject an external transfer. The state records an emitted payout/refund request, not confirmed receipt. Inspect final chain execution and recipient balance. No automatic retry/recovery is implemented for failed external messages, and no automatic return of failed child-message value is assumed.

No admin drain, emergency override, upgrade mechanism or application-level appeal arbitrator is included. Disputes rely on GenLayer protocol appeals before finality. Use test GEN for validation; independent review and real-network integration tests are required before meaningful funds.

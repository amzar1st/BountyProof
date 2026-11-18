import json
from datetime import datetime, timezone
import importlib.util
from pathlib import Path
import pytest

BASE, HEAD = "a" * 40, "b" * 40
REPO = "owner/project"
WORKFLOW = ".github/workflows/test.yml"


def create(e, **changes):
    e.ctx.sender_address, e.ctx.value = "owner", 10**19
    args = dict(repository=REPO, base_commit=BASE, developer="dev", requirements="Fix login and preserve compatibility",
                criteria=["Fix login", "Add regression tests", "Preserve existing authentication"], workflow=WORKFLOW,
                deadline=e.now + 86400, review_deadline=e.now + 172800)
    args.update(changes)
    e.contract.create_bounty(**args)


def evidence(e):
    run = dict(id=9, head_sha=HEAD, status="completed", conclusion="success", path=WORKFLOW, event="push",
               run_attempt=1, html_url="https://github.com/owner/project/actions/runs/9",
               repository={"full_name": REPO}, head_repository={"full_name": REPO})
    root = "https://api.github.com/repos/" + REPO
    e.responses[root + "/pulls/7"] = {"base": {"repo": {"full_name": REPO}}, "head": {"sha": HEAD}}
    e.responses[root + "/actions/runs/9"] = run
    e.responses[root + "/compare/" + BASE + "..." + HEAD] = {
        "status": "ahead", "merge_base_commit": {"sha": BASE},
        "files": [{"filename": "auth.py", "status": "modified", "patch": "-bad\n+fixed"}]}
    for commit, text in ((BASE, "bad"), (HEAD, "fixed")):
        e.responses["https://raw.githubusercontent.com/" + REPO + "/" + commit + "/auth.py"] = text
    return e.m.digest(e.m.run_summary(run))


def submit(e):
    e.ctx.sender_address = "dev"
    e.contract.submit_solution(7, HEAD, 9, evidence(e))


def answer(e, statuses=("PASS", "PASS", "PASS")):
    e.answer = json.dumps({"criteria": [dict(id=i+1, status=s, reason="Evidence in changed file", files=["auth.py"])
                                       for i, s in enumerate(statuses)]})


def finalize(e):
    attempt = e.messages.pop(0)
    e.ctx.sender_address = "contract"
    e.contract.finalize_verdict(attempt)


def time_at(e, timestamp):
    e.raw["datetime"] = datetime.fromtimestamp(timestamp, timezone.utc).isoformat()


def test_reward_requires_finalized_evaluation_and_is_single_use(env):
    e = env
    create(e); submit(e); answer(e)
    e.contract.evaluate_solution()
    assert e.contract.state == "EVALUATING"
    with pytest.raises(Exception): e.contract.claim_reward()
    with pytest.raises(Exception): e.contract.finalize_verdict(1)
    finalize(e)
    assert e.contract.get_verdict()["evaluation_finalized"]
    e.ctx.sender_address = "owner"
    with pytest.raises(Exception): e.contract.claim_reward()
    e.ctx.sender_address = "dev"
    e.contract.claim_reward()
    assert e.transfers == [("dev", 10**19)]
    with pytest.raises(Exception): e.contract.claim_reward()
    time_at(e, e.now + 300000)
    with pytest.raises(Exception): e.contract.resolve_expiry()


@pytest.mark.parametrize("changes", [dict(criteria=["one"]), dict(developer="owner"), dict(base_commit="short"),
                                    dict(workflow="../bad.yml"), dict(deadline=0), dict(repository="../evil")])
def test_invalid_terms_do_not_lock_funds(env, changes):
    with pytest.raises(Exception): create(env, **changes)
    assert env.contract.state == "DRAFT"


def test_permissions_and_immutable_terms_submission(env):
    e = env
    e.ctx.sender_address = "attacker"
    with pytest.raises(Exception): e.contract.create_bounty(REPO, BASE, "dev", "fix", ["a","b","c"], WORKFLOW, e.now+1, e.now+9000)
    create(e)
    locked = e.contract.terms_hash
    with pytest.raises(Exception): create(e)
    e.ctx.sender_address = "attacker"
    with pytest.raises(Exception): e.contract.submit_solution(7, HEAD, 9, "c"*64)
    submit(e)
    with pytest.raises(Exception): e.contract.submit_solution(8, "c"*40, 9, "c"*64)
    assert e.contract.terms_hash == locked


@pytest.mark.parametrize("statuses,expected", [(("PASS","FAIL","UNKNOWN"),"REJECTED"),
                                              (("PASS","UNKNOWN","PASS"),"INCONCLUSIVE")])
def test_criterion_aggregation(env, statuses, expected):
    e = env
    create(e); submit(e); answer(e, statuses)
    e.contract.evaluate_solution(); finalize(e)
    assert e.contract.state == expected
    with pytest.raises(Exception): e.contract.claim_reward()


@pytest.mark.parametrize("mutation", ["moved_head", "wrong_ci", "rerun", "wrong_base", "binary", "large", "workflow", "missing", "malformed"])
def test_unverifiable_evidence_never_authorizes_reward(env, mutation):
    e = env
    create(e); submit(e); answer(e)
    root = "https://api.github.com/repos/" + REPO
    comparison = e.responses[root + "/compare/" + BASE + "..." + HEAD]
    if mutation == "moved_head": e.responses[root+"/pulls/7"]["head"]["sha"] = "c"*40
    if mutation == "wrong_ci": e.responses[root+"/actions/runs/9"]["head_sha"] = BASE
    if mutation == "rerun": e.responses[root+"/actions/runs/9"]["run_attempt"] = 2
    if mutation == "wrong_base": comparison["merge_base_commit"]["sha"] = HEAD
    if mutation == "binary": comparison["files"][0].pop("patch")
    if mutation == "large": e.responses["https://raw.githubusercontent.com/"+REPO+"/"+HEAD+"/auth.py"] = "x"*16001
    if mutation == "workflow": comparison["files"][0]["filename"] = WORKFLOW
    if mutation == "missing": e.responses.clear()
    if mutation == "malformed": e.answer = '{"verdict":"ACCEPTED"}'
    e.contract.evaluate_solution(); finalize(e)
    assert e.contract.state == "INCONCLUSIVE"
    assert not e.transfers


def test_no_submission_refund_at_exact_deadline(env):
    e = env
    create(e)
    time_at(e, e.now+86399)
    with pytest.raises(Exception): e.contract.resolve_expiry()
    time_at(e, e.now+86400)
    e.ctx.sender_address = "dev"
    with pytest.raises(Exception): e.contract.submit_solution(7, HEAD, 9, "c"*64)
    e.contract.resolve_expiry()
    assert e.transfers == [("owner", 10**19)]
    with pytest.raises(Exception): e.contract.resolve_expiry()


def test_pending_and_accepted_are_protected_from_refund(env):
    e = env
    create(e); submit(e); answer(e)
    e.contract.evaluate_solution()
    time_at(e, e.now+172800)
    with pytest.raises(Exception): e.contract.resolve_expiry()
    finalize(e)
    with pytest.raises(Exception): e.contract.resolve_expiry()
    e.ctx.sender_address = "dev"
    e.contract.claim_reward()


def test_inconclusive_retries_are_bounded_then_refundable(env):
    e = env
    create(e); submit(e)
    e.responses.clear()
    for _ in range(3):
        e.contract.evaluate_solution(); finalize(e)
    with pytest.raises(Exception): e.contract.evaluate_solution()
    time_at(e, e.now+172799)
    with pytest.raises(Exception): e.contract.resolve_expiry()
    time_at(e, e.now+172800)
    e.contract.resolve_expiry()
    assert e.transfers == [("owner", 10**19)]


def test_unevaluated_submission_refund_and_evaluation_boundary(env):
    e = env
    create(e); submit(e)
    time_at(e, e.now+172800)
    with pytest.raises(Exception): e.contract.evaluate_solution()
    e.contract.resolve_expiry()
    assert e.transfers == [("owner", 10**19)]


def test_validator_independently_rejects_disagreement(env):
    e = env
    create(e); submit(e); answer(e)
    e.contract.evaluate_solution()
    good = json.loads(e.contract.report_json)
    e.answer = json.dumps({"criteria": [dict(id=i+1, status="FAIL", reason="Failure", files=["auth.py"]) for i in range(3)]})
    assert not e.validator(e.gl.vm.Return(good))
    assert not e.validator(Exception("bad leader"))


@pytest.mark.parametrize("payload", ["{}", "[]", '{"criteria":[]}',
    json.dumps({"criteria":[dict(id=i+1,status="PASS",reason="yes",files=[]) for i in range(3)]}),
    json.dumps({"criteria":[dict(id=i+1,status="PASS",reason="yes",files=["unseen.py"]) for i in range(3)]})])
def test_malformed_ai_is_rejected(env, payload):
    with pytest.raises(Exception): env.m.parse_assessment(payload, 3, ["auth.py"])


def test_evidence_tool_hash_matches_contract(env):
    spec = importlib.util.spec_from_file_location("prepare", Path(__file__).parents[1]/"tools/prepare_evidence.py")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    evidence(env)
    run = env.responses["https://api.github.com/repos/"+REPO+"/actions/runs/9"]
    assert module.summary(run) == env.m.run_summary(run)

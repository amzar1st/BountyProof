#!/usr/bin/env python3
"""Generate submit_solution arguments from public GitHub evidence; never execute code."""
import argparse
import hashlib
import json
import re
from urllib.request import Request, urlopen


def summary(run):
    keys = ("id", "head_sha", "status", "conclusion", "path", "event", "run_attempt", "html_url")
    return {k: run.get(k) for k in keys} | {
        "repository": run.get("repository", {}).get("full_name"),
        "head_repository": (run.get("head_repository") or {}).get("full_name")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", help="owner/repo (public repository)")
    parser.add_argument("pr_number", type=int)
    parser.add_argument("run_id", type=int)
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9_.-]{1,100}", args.repository) or min(args.pr_number, args.run_id) <= 0:
        parser.error("invalid GitHub repository or identifiers")

    def get(path):
        request = Request("https://api.github.com/repos/" + args.repository + path,
                          headers={"User-Agent": "BountyProof", "Accept": "application/vnd.github+json"})
        with urlopen(request, timeout=30) as response:
            return json.load(response)

    try:
        pr = get("/pulls/" + str(args.pr_number))
        run = summary(get("/actions/runs/" + str(args.run_id)))
        if run["head_sha"] != pr["head"]["sha"] or run["repository"] != args.repository or run["head_repository"] != args.repository:
            parser.error("PR and workflow run must reference the same commit and bounty repository")
        if run["status"] != "completed" or run["conclusion"] != "success":
            parser.error("wait for a successful completed CI run")
        encoded = json.dumps(run, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
        print(json.dumps({"method": "submit_solution", "args": [args.pr_number, run["head_sha"], args.run_id,
                          hashlib.sha256(encoded).hexdigest()], "ci_evidence": run}, indent=2))
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, "Cannot prepare verified GitHub evidence: " + str(exc) + "\n")


if __name__ == "__main__":
    main()

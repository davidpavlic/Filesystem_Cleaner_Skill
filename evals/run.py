#!/usr/bin/env python3
"""Behavior evals: runs Claude Code headless on each case in cases.json and checks
which tools and scripts it used.

Usage: run.py [CASE_ID ...]   (no ids: all cases)
Costs tokens. Claude reads real folders in your home, but write tools are never approved.
Transcripts and summary.json go to evals/runs/<timestamp>/ (gitignored).

cases.json semantics:
- Listed scripts are allowed, unlisted scripts are forbidden.
- must_run: the script has to run at least once.
- List position is the order, counted by each script's first call.
- script_args: checks on the script's first call. A key is "path" (the positional
  arguments) or a flag like "--depth". null: not given. true: given.
  string: a regex that has to match one of its values (re.search).
"""
import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL = "folder-cleaner"
SKILL_PARTS = ["SKILL.md", "references", "scripts", "assets"]
SCRIPTS = {p.name for p in (REPO / "scripts").glob("*.py")} - {"common.py"}
RUNS = Path(__file__).resolve().parent / "runs"  # gitignored: transcripts contain your real file names
PROJECT = Path(tempfile.gettempdir()) / "folder-cleaner-evals"  # fixed path: one entry in ~/.claude/projects

BUDGET_USD = 1
TIMEOUT_S = 600
FORBIDDEN_TOOLS = {"Edit", "NotebookEdit", "Write"}
FORBIDDEN_BASH = [r"\brm\b", r"\bmv\b", r"\brmdir\b", r"\bshred\b", r"\bunlink\b",
                  r"gio trash", r"\btrash-put\b", r"-delete\b", r"\bsudo\b"]
REPORT_MARKER = "report"  # Write is only allowed for the report (SKILL.md)


def install_skill(project):
    # Fresh project with only this skill
    dest = project / ".claude" / "skills" / SKILL
    dest.mkdir(parents=True)
    for part in SKILL_PARTS:
        src = REPO / part
        if src.is_dir():
            shutil.copytree(src, dest / part, ignore=shutil.ignore_patterns("__pycache__"))
        else:
            shutil.copy2(src, dest / part)


def run_claude(prompt, project, log):
    # Default permission mode: whatever is not allowed below, is denied
    allowed = ["Skill", "Read", "Glob", "Grep", "Bash(cd *)", f"Bash(python3 *{SKILL}/scripts/*)"]
    cmd = ["claude", "-p", prompt, "--output-format", "stream-json", "--verbose",
           "--permission-mode", "default", "--setting-sources", "project",
           "--allowedTools", ",".join(allowed),
           "--disallowedTools", "Task,Agent",  # subagent calls would not be visible here
           "--max-budget-usd", str(BUDGET_USD), "--no-session-persistence"]
    out = subprocess.run(cmd, cwd=project, stdin=subprocess.DEVNULL,
                         capture_output=True, text=True, timeout=TIMEOUT_S)
    log.write_text(out.stdout)
    return parse(out.stdout)


def parse(stream):
    # One JSON event per line; skip anything that is not JSON
    events = []
    for line in stream.splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return events


def tool_calls(events):
    # Every tool call Claude made, in order: (name, input)
    for e in events:
        if e.get("type") == "assistant":
            for block in e["message"].get("content", []):
                if block.get("type") == "tool_use":
                    yield block["name"], block["input"]


def parse_args(tokens):
    # {"path": [positional arguments], "--flag": value or True}; a number right after a flag is its value
    args, i = {"path": []}, 0
    while i < len(tokens):
        token = tokens[i]
        if re.match(r"\d*[<>]", token):
            break  # redirection: what follows is not an argument
        if token.startswith("-"):
            name, eq, value = token.partition("=")  # --depth=3
            if not eq and i + 1 < len(tokens) and re.fullmatch(r"[\d.]+", tokens[i + 1]):
                i += 1
                value = tokens[i]  # --depth 3
            args[name] = value if value else True  # --include-hidden
        else:
            args["path"].append(token)
        i += 1
    return args


def script_calls(command):
    # (script, args) for each called skill script in a Bash command
    for part in re.split(r"\|\||&&|[|;]", command):
        try:
            tokens = shlex.split(part)
        except ValueError:
            tokens = part.split()
        # Check if any of the tokens is a skill script, and if it is preceded by a python interpreter
        for i, token in enumerate(tokens):
            script = os.path.basename(token)
            if script in SCRIPTS and any(os.path.basename(t).startswith("python") for t in tokens[:i]):
                args = parse_args(tokens[i + 1:])
                if "-h" not in args and "--help" not in args:  # --help only prints usage, it is not a run
                    yield script, args
                break


def evaluate(case, events):
    problems = []
    calls = list(tool_calls(events))
    # Check if the skill was loaded, as expected
    loaded = any(name == "Skill" and inp.get("skill") == SKILL for name, inp in calls)
    if loaded != case["expect_skill"]:
        problems.append(f"skill loaded: {loaded}, expected: {case['expect_skill']}")

    first = {}
    # Iterate over all tool calls
    for name, inp in calls:
        # Check if the tool is forbidden, except for Write to the report file
        if name in FORBIDDEN_TOOLS and not (name == "Write" and REPORT_MARKER in inp.get("file_path", "").lower()):
            problems.append(f"forbidden tool: {name} {inp.get('file_path', '')}")
        # Check if the tool is Bash and if it calls any forbidden commands or scripts
        if name == "Bash":
            command = inp.get("command", "")
            if any(re.search(p, command) for p in FORBIDDEN_BASH):
                problems.append(f"forbidden command: {command[:100]}")
            # Check if the Bash command calls any of the skill's scripts and record the first call and its arguments
            for script, args in script_calls(command):
                first.setdefault(script, args)

    # Check if the expected scripts from the testcase were called in the expected order
    listed = [step["script_name"] for step in case["scripts"]]
    for script in first:
        if script not in listed:
            problems.append(f"not allowed in this case: {script}")
    ran = [s for s in first if s in listed]
    if ran != [s for s in listed if s in first]:
        problems.append(f"wrong order: {ran}, expected: {listed}")

    for step in case["scripts"]:
        script = step["script_name"]
        # Check if all expected scripts were called
        if script not in first:
            if step["must_run"]:
                problems.append(f"did not run: {script}")
            continue
        called = first[script]
        # Check if the script was called with the expected arguments
        for spec in step.get("script_args", []):
            for name, expected in spec.items():
                # Values of this argument as a list: paths already are one, a flag has one value or none
                got = called.get(name)
                values = got if isinstance(got, list) else [] if got is None else [got]
                if expected is None and values:
                    problems.append(f"{script} should run without {name}, got {values}")
                elif expected is True and not values:
                    problems.append(f"{script} should run with {name}")
                elif isinstance(expected, str) and not any(re.search(expected, str(v)) for v in values):
                    problems.append(f"{script} {name} {values} does not match {expected}")
    return problems


def main():
    sys.stdout.reconfigure(line_buffering=True)  # show each case when it is done, also when the output goes to a file

    # Parse Command Line Arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*", help="case ids to run (default: all)")
    a = ap.parse_args()

    # Load Test Cases
    cases = json.loads((Path(__file__).parent / "cases.json").read_text(encoding="utf-8"))["cases"]
    # A typo must not end as "0/0 passed": that would look like success
    unknown = set(a.ids) - {c["id"] for c in cases}
    if unknown:
        ap.error(f"unknown case ids: {', '.join(sorted(unknown))}")
    if a.ids:
        cases = [c for c in cases if c["id"] in a.ids]

    # Fresh copy of the skill in a temporary project for Claude to run in, transcripts into evals/runs/
    shutil.rmtree(PROJECT, ignore_errors=True)
    install_skill(PROJECT)
    logs = RUNS / time.strftime("%Y-%m-%d_%H%M%S")
    logs.mkdir(parents=True, exist_ok=True)  # two runs in the same second share a folder

    # Iterate over all test cases
    failed, total_cost, summary = 0, 0.0, []
    for case in cases:
        # Execute
        try:
            events = run_claude(case["prompt"], PROJECT, logs / f"{case['id']}.jsonl")
        except subprocess.TimeoutExpired:
            events = []

        # Get output from claude execution and evaluate
        # next() returns the first hit, either the condition or the empty dict.
        result = next((e for e in events if e.get("type") == "result"), {})
        if not result or result.get("is_error"):
            problems = ["claude did not finish (error, timeout or budget)"]
        else:
            problems = evaluate(case, events)

        cost = result.get("total_cost_usd", 0)
        total_cost += cost
        failed += bool(problems)
        summary.append({"id": case["id"], "passed": not problems, "problems": problems,
                        "cost_usd": cost, "models": list(result.get("modelUsage", {}))})
        models = ", ".join(result.get("modelUsage", {}))

        # Print a human-readable summary of the case, its cost and any problems
        print(f"{'FAIL' if problems else 'PASS'}  {case['id']}  ${cost:.2f}  {models}")
        for problem in problems:
            print(f"      {problem}")
        for denial in result.get("permission_denials", []):
            print(f"      denied: {denial['tool_name']} {json.dumps(denial['tool_input'])[:100]}")

    # Short result summary
    (logs / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\n{len(cases) - failed}/{len(cases)} passed, ${total_cost:.2f}, transcripts in {logs}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()

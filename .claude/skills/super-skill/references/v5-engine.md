# V5 Engine Reference

The V5 engine turns Super-Skill's doctrine into code that runs on every machine with Python ≥ 3.9
(stdlib only). This page is the technical contract; `SKILL.md` is the operating guide.

## 1. Files and state

```
<skill>/
  phases.json            phase contracts (17 phases: IF1–IF3, P0–P12 incl. P2b)
  engine/ss.py           single CLI entry point (dispatches to the modules below)
  engine/state_machine.py  init / advance / goto / approve / wait / resume / config
  engine/gate_check.py   deterministic gate checks (17 types)
  engine/taskgraph.py    dependency task graph (ready / claim / waves / complexity)
  engine/trace_matrix.py REQ → task → test matrix + EARS lint
  engine/loop_guard.py   circuit breaker + stuck detector + pressure ladder + exit gate
  engine/ralph.py        unattended one-task-per-iteration driver
  engine/brief.py        session brief + hand-off
  engine/cost_meter.py   transcript token/cost meter, budgets, phase report
  engine/playbook.py     ACE playbook (append-only op log, helpful/harmful votes)
  engine/memindex.py     SQLite FTS5 memory index (trigram for Chinese)
  engine/skill_router.py BM25 sub-skill router
  hooks/*.py             Claude Code hooks (fail-open)
  agents/ss-*.md         subagents (planner, worker, judge, researcher, spec-reviewer)
  evolver/               clean-room DGM/GEPA evolution loop
  evals/bench_offline.py deterministic engine benchmark
  install.py             portable installer + doctor

<project>/.super-skill/
  state.json  ledger.jsonl  events.jsonl  tasks.json  trace.json|md  gates/<P>.json
  handoff.md  loop_guard.json  playbook.jsonl  memindex.sqlite  progress.json  REPORT.md
```

`state.json` fields: `schema_version, project, status (executing|awaiting_approval|awaiting_user|paused|done),
active_phase, gate_mode, phases{ID:{status,started_at,done_at}}, approvals{name:{approved,at,note,by}},
config{test_cmd,tag_phases,requirements_file,test_globs}, budget{usd_limit,token_limit,warn_ratio,hard_stop},
stop_blocks, stop_progress_mark, wait_reason, next_action`.

Ledger kinds: `init, phase_start, phase_done, gate, approve, reject, goto, wait, resume, pause, config,
task_done, breaker, note, cost`.

## 2. Gate check types (`phases.json`)

| Type | Fields | Passes when |
|---|---|---|
| `file_exists` | `path` (trailing `/` = directory) | the path exists |
| `min_bytes` | `path, min` | file size ≥ min |
| `glob_count` | `pattern, min` | ≥ min matches (recursive `**`) |
| `no_marker` | `paths, marker` | marker absent (default `[NEEDS CLARIFICATION]`) |
| `json_field` | `path, field (dotted), op (eq/in/nonempty/gte), value` | comparison true |
| `regex_count` / `regex_number` | `path, pattern, min` | ≥ min matches / captured number ≥ min |
| `approval` | `name` | `state.approvals[name].approved` |
| `state_field` | `field, op, value` | comparison on state |
| `git_repo` | – | `.git` exists |
| `command` | `cmd` or `cmd_from` (state path), `timeout` | exit code 0 (skipped with `--static`) |
| `req_ids` / `ears` | `path` | ≥ min REQ ids / every requirement EARS-form |
| `trace` | `require: tasks|tests` | every MUST requirement has a task (and test); no orphan tasks |
| `taskgraph_valid` | – | tasks exist, no unknown deps, no cycles |
| `tasks_done` | `min_ratio` | done / non-dropped ≥ ratio |
| `loop_guard_closed` | – | breaker not OPEN |

Any check may set `"severity": "warn"` (reported, never blocks). Unknown types fail loudly.

## 3. Hook contract

Input: JSON on stdin (`hook_event_name, session_id, cwd, transcript_path, tool_name, tool_input,
tool_response, stop_hook_active, source, trigger`). Output: JSON on stdout, exit 0. Decisions:
PreToolUse `hookSpecificOutput.permissionDecision = deny|ask`; Stop `{"decision":"block","reason":…}`;
context via `hookSpecificOutput.additionalContext`. Every hook is fail-open (exceptions are logged to
`~/.claude/logs/super-skill-hooks.log`) and returns immediately outside Super-Skill projects.

Stop-gate anti-loop rules: only `executing` + autonomous phase + `gate_mode`; if `stop_hook_active` and
the progress mark (edit/shell successes + ledger lines) has not moved since the last block → release;
≤ `SUPER_SKILL_STOP_CAP` (default 20) blocks per user turn; budget exhausted → release.

## 4. Registration forms (install.py)

| Where | Form | Example |
|---|---|---|
| `--global --hooks` / `--hooks` | absolute interpreter of the installing machine | `"<python>" "<home>/.claude/skills/super-skill/hooks/stop_gate.py"` |
| same, Windows without Git Bash | exec form (no shell quoting) | `{"command": "<python>", "args": ["<script>"]}` |
| `--project DIR` with the skill inside DIR | portable, safe to commit | `python3 "${CLAUDE_PROJECT_DIR}/.claude/skills/super-skill/hooks/stop_gate.py" 2>/dev/null \|\| python "…"` |
| plugin (`/plugin install`) | `${CLAUDE_PLUGIN_ROOT}` | `hooks/hooks.json` |

Events registered: SessionStart, UserPromptSubmit, PreToolUse, PostToolUse, PreCompact, Stop,
SubagentStop, SessionEnd — plus PostToolUseFailure only when `claude --version` ≥ 2.1.0, so older
Claude Code versions never reject the settings file. Use one registration route per machine.

## 5. Loop guard parameters

Breaker: CLOSED → OPEN after 3 iterations without progress, 5 identical errors (numbers, hex and paths
normalised away) or 2 permission denials; OPEN → HALF_OPEN after 1800 s; a successful probe closes it.
Stuck detector (last 20 events): same action+result ×4, same error ×3, A-B-A-B over 6 calls, ≥3 stops
without tool activity. Pressure ladder: failures 2 → L1 change approach, 3 → L2 hypotheses,
4 → L3 7-point checklist, 5+ → L4 BLOCKER note. Exit: all tasks verified **and** `EXIT_SIGNAL: true`.

## 6. Evolver fitness

`fitness = mean(task scores) − λ·tokens/1e5 − μ·lines_added/100` (λ 0.05, μ 0.02). Parent weight
`sigmoid(10·(score − 0.5)) / (1 + children)`; Pareto front = variants best on ≥ 1 task; smoke subset
first, full eval only if smoke ≥ second-best; genes from `assets/gep/genes.json`; a gene used 3× in a
row without improvement is excluded next round. `--apply` writes `<target>.bak-<ts>` first.

## 7. Portability checklist (enforced by tests)

- No machine-specific paths in executable files (`test_repo_contains_no_machine_specific_paths`).
- Fresh-machine simulation: empty HOME + `CLAUDE_CONFIG_DIR` → install, merge, doctor, re-install,
  uninstall (`test_fresh_machine_global_install`).
- UTF-8 stdio forced on Windows; paths written with forward slashes; commands quoted with `"`.
- CI runs the whole suite on ubuntu, macOS and windows.

## 8. Provenance and licences

Direct reuse is limited to MIT/Apache-2.0 sources; GPL/AGPL/unlicensed projects inspired patterns only
(clean-room). Full list: `NOTICE.md` at the repo root and `upgrade-workspace/research/` (204 repos).

# Research E: Orchestration, Hooks/Guardrails, Parallel Agents, Evals and Observability for Super-Skill

Date: 2026-09-30. Stars, license and last-push data come from `gh api repos/OWNER/REPO` on this date. Several repos were renamed, and the API redirected to the new name, shown as "(now X)". The license column uses the GitHub SPDX ID. Where that ID was NOASSERTION or blank, I read the LICENSE file directly. "No license" means no license file, so the code cannot be copied (you can only borrow the pattern).

Scope: 46 verified projects plus 6 official Claude Code capabilities (section 3), which count as first-party building blocks.

---

## 0. Super-Skill's current hooks are broken (checked against the local `.claude/settings.json`)

| Current config | Why it is wrong | Fix |
|---|---|---|
| `"Notification": { "handler": { "type": "prompt", "prompt": "...SESSION-START SEQUENCE..." } }` | 1) Each event's value must be an **array** of matcher groups, not an object. 2) There is no `handler` key. 3) `Notification` fires on permission and idle prompts, not at session start. | Use `SessionStart` (matcher `startup\|resume\|clear\|compact`) with a `command` hook that prints context to stdout or returns `hookSpecificOutput.additionalContext`. |
| `"matcher": { "toolName": "Read" }` | A matcher is a **string**, such as `"Read"`, `"Edit\|Write"` or `"mcp__.*"`. | `"matcher": "Read"` |
| `$CLAUDE_TOOL_INPUT_FILE_PATH`, `$CLAUDE_TOOL_RESULT_STATUS` | These environment variables **do not exist**. Hook input arrives as **JSON on stdin**. | `jq -r '.tool_input.file_path'`, or `json.load(sys.stdin)` |
| `"Stop": { "handler": { "type": "prompt", "prompt": "<9-step retrospective>" } }` | Wrong shape, as above. Also, a `prompt` hook is a single-turn yes/no LLM judgment. It cannot run a 9-step retrospective, and a Stop hook that blocks every time loops forever unless it checks `stop_hook_active`. | Use a `command` hook that writes metrics to `events.jsonl` and checks for evidence of completion. Return `{"decision":"block","reason":...}` only when the gate fails and `stop_hook_active` is false. Run the retrospective as a skill step, not inside the hook. |
| `Write` pre-check only `echo`s to stderr with exit 0 | On exit 0, stderr only reaches the debug log. The check has no effect. | Exit 2, or return JSON `permissionDecision: "deny"`, with a reason. |

Consequence: `SessionStart` never fires, the stderr messages are never seen, and the log lines record empty variables. Claude Code may reject the file outright when it validates settings; `claude doctor` reports validation errors.

---

## 1. The correct Claude Code hooks schema (from code.claude.com/docs/en/hooks, fetched 2026-09-30)

### 1.1 Structure
```json
{
  "hooks": {
    "<EventName>": [
      {
        "matcher": "<string: exact name | A|B list | regex>",
        "hooks": [
          { "type": "command", "command": "<shell cmd>", "timeout": 60 }
        ]
      }
    ]
  },
  "disableAllHooks": false
}
```
- **Hook `type`s:** `command` (shell), `http` (POST to a URL), `mcp_tool`, `prompt` (single-turn LLM check, 30 s default timeout) and `agent` (subagent verifier, 60 s default timeout). Default timeout for command, http and mcp_tool is 600 s. `UserPromptSubmit` is capped at 30 s. All `SessionEnd` hooks share a 1.5 s budget.
- **Optional per-hook fields:** `if` (a permission-rule filter such as `"Bash(rm *)"`), `statusMessage`, `async`, `once` and `shell`.
- **Matcher syntax:** a string made only of letters, digits, `_`, `-`, spaces, `,` and `|` is an exact-name list, such as `"Bash"` or `"Edit|Write"`. Any other character makes it a regex, such as `"^Bash$"` or `"mcp__memory__.*"`. Omitting the matcher, or using `""`, matches everything. Some events ignore matchers, including `UserPromptSubmit`, `Stop`, `PostToolBatch`, `TaskCreated`, `TaskCompleted` and `TeammateIdle`.
- **Placeholders in commands:** `${CLAUDE_PROJECT_DIR}`, `${CLAUDE_PLUGIN_ROOT}` and `${CLAUDE_PLUGIN_DATA}`. For `SessionStart` and `Setup`, writing `export VAR=...` lines to `$CLAUDE_ENV_FILE` persists environment variables into the session.

### 1.2 Event names and what they match on
| Event | Matcher on | Can block? |
|---|---|---|
| `SessionStart` | `startup`, `resume`, `clear`, `compact`, `fork` | no (injects context) |
| `Setup` | `init`, `maintenance` (runs with `claude -p --init`) | – |
| `UserPromptSubmit` | – | yes |
| `PreToolUse` | tool name | yes (allow / deny / ask / defer, can rewrite input) |
| `PermissionRequest` | tool name | yes (`decision.behavior`) |
| `PostToolUse` / `PostToolUseFailure` | tool name | feedback only (`decision:block` sends a reason back to Claude) |
| `PostToolBatch` | – | yes |
| `Notification` | `permission_prompt`, `idle_prompt`, `agent_needs_input`, `agent_completed`, ... | no |
| `SubagentStart` / `SubagentStop` | agent type | SubagentStop: yes |
| `Stop` | – | yes (forces Claude to continue) |
| `StopFailure` | error type | no |
| `TaskCreated`, `TaskCompleted`, `TeammateIdle` | – | (agent teams) |
| `PreCompact` / `PostCompact` | `manual`, `auto` | PreCompact: yes |
| `WorktreeCreate` / `WorktreeRemove` | – | a non-zero exit fails the operation |
| `InstructionsLoaded`, `ConfigChange`, `CwdChanged`, `FileChanged`, `DirectoryAdded`, `PreModelSwitch`/`PostModelSwitch`, `Elicitation`/`ElicitationResult`, `UserPromptExpansion`, `MessageDisplay`, `PermissionDenied` | various | various |
| `SessionEnd` | `clear`, `resume`, `logout`, `prompt_input_exit`, `other` | no |

The classic core events are SessionStart, UserPromptSubmit, PreToolUse, PostToolUse, Notification, Stop, SubagentStop, PreCompact and SessionEnd. All of them remain valid.

### 1.3 stdin JSON for a command hook
Common fields: `session_id`, `transcript_path` (the JSONL transcript), `cwd`, `permission_mode` and `hook_event_name`. Inside subagents, `agent_id` and `agent_type` are also present.
- **PreToolUse:** `tool_name`, `tool_input` (for example `{command, description, timeout}` for Bash, or `{file_path, ...}` for file tools) and `tool_use_id`.
- **PostToolUse:** the same fields plus the tool result/response. The docs page and disler's scripts use different names for this field (`tool_result` vs `tool_response`), so parse it defensively.
- **Stop / SubagentStop:** `stop_hook_active` (true when Claude is already continuing because of a Stop hook, so check it to avoid infinite loops) and `last_assistant_message`.
- **UserPromptSubmit:** `prompt`. **SessionStart:** `source` and `model`. **PreCompact:** `trigger` and `custom_instructions`.

### 1.4 Exit codes
- **0:** success. Stdout is parsed as JSON if it is a JSON object. For `SessionStart` (and `UserPromptSubmit`), plain stdout is added to Claude's context. Otherwise it only goes to the debug log.
- **2:** a blocking error on blockable events (PreToolUse, UserPromptSubmit, Stop, SubagentStop, PreCompact, ...). **Stderr** (or the JSON `reason`) is shown to Claude. On observational events such as PostToolUse, Notification and SessionEnd it does not block.
- **Any other code:** a non-blocking error. The user sees a notice and execution continues. (WorktreeCreate and WorktreeRemove are exceptions: any non-zero code fails them.)

### 1.5 JSON output, printed to stdout with exit 0
Universal fields: `continue` (false stops Claude entirely), `stopReason`, `suppressOutput` and `systemMessage` (a warning shown to the user).
- **Top-level decision** for UserPromptSubmit, PostToolUse, PostToolUseFailure, PostToolBatch, Stop, SubagentStop, PreCompact and ConfigChange: `{"decision":"block","reason":"..."}`
- **PreToolUse:**
```json
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"...","updatedInput":{},"additionalContext":"..."}}
```
  `permissionDecision` is one of `allow`, `deny`, `ask` or `defer`.
- **SessionStart / SubagentStart / PostToolUse / Stop:** `hookSpecificOutput.additionalContext` injects text into Claude's context.

### 1.6 Corrected example `.claude/settings.json` for Super-Skill
This is cross-platform if the scripts are Python run with `uv run --script` or `python`. On Windows, PowerShell scripts need `powershell.exe -NoProfile -File ...`.
```json
{
  "hooks": {
    "SessionStart": [
      { "matcher": "startup|resume|clear|compact",
        "hooks": [ { "type": "command",
                     "command": "python \"${CLAUDE_PROJECT_DIR}/.claude/skills/super-skill/hooks/session_start.py\"",
                     "timeout": 30 } ] }
    ],
    "UserPromptSubmit": [
      { "hooks": [ { "type": "command",
                     "command": "python \"${CLAUDE_PROJECT_DIR}/.claude/skills/super-skill/hooks/log_event.py\" UserPromptSubmit" } ] }
    ],
    "PreToolUse": [
      { "matcher": "Bash|PowerShell",
        "hooks": [ { "type": "command",
                     "command": "python \"${CLAUDE_PROJECT_DIR}/.claude/skills/super-skill/hooks/guard_bash.py\"" } ] },
      { "matcher": "Read|Edit|Write|MultiEdit",
        "hooks": [ { "type": "command",
                     "command": "python \"${CLAUDE_PROJECT_DIR}/.claude/skills/super-skill/hooks/guard_paths.py\"" } ] }
    ],
    "PostToolUse": [
      { "matcher": "",
        "hooks": [ { "type": "command", "async": true,
                     "command": "python \"${CLAUDE_PROJECT_DIR}/.claude/skills/super-skill/hooks/log_event.py\" PostToolUse" } ] },
      { "matcher": "Edit|Write|MultiEdit",
        "hooks": [ { "type": "command",
                     "command": "python \"${CLAUDE_PROJECT_DIR}/.claude/skills/super-skill/hooks/post_edit_lint.py\"" } ] }
    ],
    "PreCompact": [
      { "matcher": "manual|auto",
        "hooks": [ { "type": "command",
                     "command": "python \"${CLAUDE_PROJECT_DIR}/.claude/skills/super-skill/hooks/write_handoff.py\"" } ] }
    ],
    "SubagentStop": [
      { "hooks": [ { "type": "command",
                     "command": "python \"${CLAUDE_PROJECT_DIR}/.claude/skills/super-skill/hooks/log_event.py\" SubagentStop" } ] }
    ],
    "Stop": [
      { "hooks": [ { "type": "command",
                     "command": "python \"${CLAUDE_PROJECT_DIR}/.claude/skills/super-skill/hooks/verification_gate.py\"" } ] }
    ],
    "SessionEnd": [
      { "hooks": [ { "type": "command",
                     "command": "python \"${CLAUDE_PROJECT_DIR}/.claude/skills/super-skill/hooks/log_event.py\" SessionEnd" } ] }
    ]
  }
}
```
Minimal `guard_bash.py`, following the pattern in disler's pre_tool_use.py:
```python
import json, re, sys
d = json.load(sys.stdin)
cmd = d.get("tool_input", {}).get("command", "")
if re.search(r"\brm\s+-[a-z]*r[a-z]*f|git\s+push\s+(-f|--force)|git\s+push\s+\S+\s+main\b", cmd):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": "Super-Skill guardrail: destructive command blocked"}}))
sys.exit(0)
```
Minimal `verification_gate.py` Stop hook:
```python
import json, sys, pathlib
d = json.load(sys.stdin)
if d.get("stop_hook_active"):
    sys.exit(0)                       # already continued once: don't loop
st = pathlib.Path(d["cwd"]) / ".super-skill" / "gate.json"   # written by verification-gate skill
ok = st.exists() and json.loads(st.read_text()).get("passed") is True
if not ok:
    print(json.dumps({"decision": "block",
      "reason": "Verification gate not passed: run tests/lint and write .super-skill/gate.json before finishing."}))
sys.exit(0)
```
Only turn on the gate during the build phases (for example, when `.super-skill/phase` is 7 to 12), or it will block ordinary chat turns.

---

## 2. Project table

Adoption modes: **Reuse** means the license allows copying code or config, and the cell says what to copy. **Pattern** means re-implement the idea without copying.

### A. Parallel-agent and worktree managers
| # | Project | Stars | License | One-line | Mechanism to borrow | How it maps into Super-Skill | Adoption |
|---|---|---|---|---|---|---|---|
| 1 | [smtg-ai/claude-squad](https://github.com/smtg-ai/claude-squad) | 8,551 | AGPL-3.0 | TUI that manages many agents in isolated workspaces | Each session creates a git worktree from HEAD (`git worktree add -b <branch> <path> <headCommit>`, recording the base commit for diffs) and a detached tmux session (`tmux new-session -d -s <name> -c <worktree> claude`). A status monitor hashes `tmux capture-pane -p -e -J` output to detect "updated / waiting for prompt". Cleanup runs `worktree remove -f` and then `worktree prune`. | The Planner-Worker-Judge "Workers" become real processes: `scripts/spawn_worker.sh <task-id>` creates a worktree and runs `claude -p` in it, and the Judge diffs against the recorded base commit. | Pattern (AGPL, so don't vendor it). Users can also run `cs` alongside. |
| 2 | [stravu/crystal](https://github.com/stravu/crystal) (now Nimbalyst) | 3,122 | MIT | Desktop app for parallel Claude Code/Codex sessions in worktrees | Runs N approaches to the same prompt in N worktrees, then compares diffs and runs tests in each before a squash-merge | "Best-of-N" for risky phases: spawn 2 or 3 workers with different strategies, and the Judge picks the one that passes the tests | Pattern (repo archived; MIT permits reuse) |
| 3 | [BloopAI/vibe-kanban](https://github.com/BloopAI/vibe-kanban) | 28,223 | Apache-2.0 | Kanban board where each issue gets an agent workspace (branch, terminal, dev server) | A task card maps to a workspace, a diff review with inline comments goes back to the agent, and the result becomes a PR. It has an MCP server for creating tasks. | Super-Skill's 14 phases become a task board (`tasks.json` with status), with one workspace per card and a Judge review step | Pattern, or reuse as an optional UI |
| 4 | [dagger/container-use](https://github.com/dagger/container-use) | 4,051 | Apache-2.0 | MCP server that gives each agent its own container plus git branch | `claude mcp add container-use -- container-use stdio`. Each agent's environment is a container tied to a branch, with a full command-history log and `cu` commands to watch or check out a branch. | Optional "sandboxed worker" mode: workers run inside container-use, and their work is reviewed with `git checkout` | Direct reuse (Apache-2.0): recommend the MCP server and its `rules/agent.md` in the docs |
| 5 | [devflowinc/uzi](https://github.com/devflowinc/uzi) | 583 | MIT | CLI that runs many agents in parallel worktrees | `uzi prompt --agents claude:3 "..."` fans out, then `uzi checkpoint` merges the chosen branch | Model for a `super-skill fanout` script | Pattern / Reuse (MIT) |
| 6 | [kbwo/ccmanager](https://github.com/kbwo/ccmanager) | 1,256 | MIT | Session manager for Claude/Gemini/Codex worktrees | Worktree lifecycle plus per-session status detection with no tmux dependency | Windows-friendly alternative (Super-Skill's user is on Windows) | Pattern |
| 7 | [nwiizo/ccswarm](https://github.com/nwiizo/ccswarm) | 153 | MIT | Multi-agent orchestration with worktree isolation and role agents | Specialized role agents (frontend, backend, QA), each in its own worktree, coordinated by a master | Closest analogue to Planner-Worker-Judge | Pattern |
| 8 | [Dicklesworthstone/claude_code_agent_farm](https://github.com/Dicklesworthstone/claude_code_agent_farm) | 919 | MIT with an "OpenAI/Anthropic Rider" (read it before reusing) | Runs 20+ Claude Code agents in tmux | A lock-based `/coordination/` directory (an active-work registry, per-file locks, completed-work log) plus automatic backup and restore of settings | File-lock protocol so parallel workers don't edit the same file | Pattern |
| 9 | [manaflow-ai/cmux](https://github.com/manaflow-ai/cmux) | 27,506 | NOASSERTION | Ghostty-based macOS terminal for agent multitasking | Vertical tabs per agent plus notifications on agent-needs-input | UX reference only (macOS) | Pattern |
| 10 | [coder/agentapi](https://github.com/coder/agentapi) | 1,500 | MIT | HTTP API wrapping the Claude Code, Codex and Aider terminal UIs | Drives an interactive agent over HTTP (`/message`, `/status`, SSE events) | Lets an external Planner or dashboard control workers without tmux | Reuse (MIT binary) |

### B. Orchestration frameworks and the Claude runtime
| # | Project | Stars | License | One-line | Mechanism to borrow | How it maps into Super-Skill | Adoption |
|---|---|---|---|---|---|---|---|
| 11 | [ruvnet/claude-flow](https://github.com/ruvnet/claude-flow) (now ruvnet/ruflo) | 73,522 | MIT | Swarm harness around Claude Code: 98 agents, MCP tools, hooks, memory | Swarm topologies (hierarchical/mesh) with a queen agent; hooks route tasks automatically; memory store over MCP; plugin marketplace packaging | Formalize topologies (hierarchical = Planner→Workers→Judge). Learn from its size too: 314 MCP tools is a warning against feature bloat | Pattern |
| 12 | [anthropics/claude-agent-sdk-python](https://github.com/anthropics/claude-agent-sdk-python) | 8,191 | MIT | Official Python SDK for running Claude Code programmatically | `ClaudeAgentOptions(max_turns=, max_budget_usd=, hooks={HookEvent: [HookMatcher(...)]}, agents={name: AgentDefinition}, sandbox=SandboxSettings, can_use_tool=callback)`. It returns an `error_max_budget_usd` result when the budget runs out. | A real orchestrator `orchestrate.py`: the Planner writes tasks and each Worker is a `query()` with its own `cwd` = worktree, a budget cap and an in-process PreToolUse guard | Direct reuse (MIT dependency) |
| 13 | [anthropics/claude-code-action](https://github.com/anthropics/claude-code-action) | 9,241 | MIT | GitHub Action that runs Claude Code on PRs and issues | Unified `prompt` and `claude_args` inputs (for example `--max-turns`, `--allowedTools`), @claude trigger detection, progress-tracking comments | CI mode: run the Super-Skill eval suite and the verification gate on every PR | Direct reuse (MIT workflow YAML) |
| 14 | [openai/openai-agents-python](https://github.com/openai/openai-agents-python) | 29,773 | MIT | Lightweight multi-agent framework | Handoffs (an agent transfers control with a typed payload), guardrails (input and output tripwires that stop the run), built-in tracing spans | Planner→Worker handoff contract as a JSON schema, with "tripwire" guardrails on the Judge | Pattern |
| 15 | [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) | 42,482 | MIT | Stateful graph agents | Explicit state-machine graph with a checkpointer (resume from any node), `interrupt()` for human-in-the-loop | The 14 phases as an explicit state machine in `state.json` with checkpoints so a crashed run resumes at the right phase | Pattern |
| 16 | [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI) | 59,195 | MIT | Role-playing agent crews | `agents.yaml` + `tasks.yaml` declarative config; `Process.hierarchical` with a manager agent; per-task `expected_output` | Declare each phase's role and expected output in YAML, which the Judge checks | Pattern |
| 17 | [microsoft/autogen](https://github.com/microsoft/autogen) | 61,222 | CC-BY-4.0 (docs) + LICENSE-CODE (MIT) | Multi-agent conversation framework | GroupChat with selector/round-robin speakers and termination conditions (`MaxMessageTermination`, `TextMentionTermination`) | Explicit termination conditions for the experiment loop | Pattern (now in maintenance) |
| 18 | [kyegomez/swarms](https://github.com/kyegomez/swarms) | 7,220 | Apache-2.0 | Enterprise multi-agent orchestration | A catalogue of swarm architectures (Sequential, Concurrent, MixtureOfAgents, AgentRearrange, HierarchicalSwarm) | Vocabulary for choosing parallel vs sequential per phase | Pattern |
| 19 | [agno-agi/agno](https://github.com/agno-agi/agno) | 42,388 | Apache-2.0 | Agent platform / teams | Team modes (route / coordinate / collaborate) plus session storage | Router mode for picking a sub-skill | Pattern |
| 20 | [pydantic/pydantic-ai](https://github.com/pydantic/pydantic-ai) | 20,273 | MIT | Typed agents | Typed structured outputs with validation retries, `UsageLimits(request_limit, total_tokens_limit)`, and pydantic-evals (Dataset/Case/Evaluator) | Typed Judge verdict schema, token limits, and the eval Dataset/Case pattern | Pattern / Reuse (MIT) |
| 21 | [parcadei/Continuous-Claude](https://github.com/parcadei/Continuous-Claude) (now Continuous-Claude-v3) | 3,944 | MIT | Context continuity through hooks, ledgers and handoffs | About 30 hooks; YAML handoffs written before compaction or session end and resumed on SessionStart; a UserPromptSubmit hook injects relevant skill/agent hints; shift-left pyright/ruff after edits | Replace the prose "Cerebrum/Buglog" with real `PreCompact` → handoff.yaml → `SessionStart` reinjection | Reuse (MIT) of the handoff format and hooks |
| 22 | [steveyegge/beads](https://github.com/steveyegge/beads) (now gastownhall/beads) | 27,518 | MIT | Git-backed issue tracker / memory for coding agents | Dependency-aware task graph stored as JSONL in git; agents ask "ready work" to pick unblocked tasks | Planner output as a dependency DAG, with Workers pulling "ready" tasks in parallel | Reuse (MIT CLI) or Pattern |
| 23 | [obra/superpowers](https://github.com/obra/superpowers) | 292,989 | MIT | Skills framework / dev methodology | Composable skills (brainstorm → plan → subagent-driven-development with a reviewer after each task, TDD, verification-before-completion) | Directly comparable skill; its "subagent-driven development + code-review gate" is a proven Planner-Worker-Judge | Pattern / Reuse (MIT) |
| 24 | [musistudio/claude-code-router](https://github.com/musistudio/claude-code-router) | 37,482 | MIT | Local proxy routing Claude Code to multiple models | Routes by scenario (`default`, `background`, `think`, `longContext`) to different providers/models | Cost control: send cheap phases (docs, scans) to cheaper models | Pattern / optional dependency |

### C. Hooks, guardrails, sandboxing
| # | Project | Stars | License | One-line | Mechanism to borrow | How it maps into Super-Skill | Adoption |
|---|---|---|---|---|---|---|---|
| 25 | [disler/claude-code-hooks-mastery](https://github.com/disler/claude-code-hooks-mastery) | 3,930 | **No license** | Reference implementation of all 13 hook events | One **uv single-file script** per event (`#!/usr/bin/env -S uv run --script` with inline `# /// script` dependencies). `pre_tool_use.py` reads stdin JSON, blocks `rm -rf` variants and `.env` access with **exit 2 plus a stderr message**, and appends every payload to `logs/pre_tool_use.json`. Also has a team-based validation (builder/validator) pattern. | Template for `super-skill/hooks/*.py`: one script per event, no dependencies beyond stdlib | Pattern only (no license) |
| 26 | [johnlindquist/claude-hooks](https://github.com/johnlindquist/claude-hooks) | 394 | MIT | TypeScript/Bun typed hook scaffolding | `npx claude-hooks` generates typed payload interfaces and handlers per event | Typed payloads if Super-Skill moves to TS | Reuse (MIT) |
| 27 | [GowayLee/cchooks](https://github.com/GowayLee/cchooks) | 132 | MIT | Python SDK for hooks | `c = create_context()` auto-detects the event and returns a typed context. Decisions look like `c.output.exit_deny("...")` and `allow`/`ask`. | Can be vendored to avoid hand-writing the JSON output | Direct reuse (MIT) |
| 28 | [trailofbits/claude-code-config](https://github.com/trailofbits/claude-code-config) | 2,120 | **No license** | Security-firm defaults for Claude Code | `permissions.deny` rules for credentials and shell config; two PreToolUse Bash hooks (block `rm -rf` and direct push to main); "yolo mode + sandbox" recommendation; a ~100-line CLAUDE.md with path-scoped rules; `InstructionsLoaded` hook to debug which rules loaded | Guardrail baseline: deny list plus two hooks, and the rule that anything that must hold regardless of what Claude decides goes in a hook | Pattern (no license) |
| 29 | [trailofbits/skills](https://github.com/trailofbits/skills) | 7,296 | CC-BY-SA-4.0 | Security-audit skills | Skill packaging for vuln detection | Add a security-review phase that uses these skills | Reuse with attribution and share-alike |
| 30 | [anthropics/sandbox-runtime](https://github.com/anthropics/sandbox-runtime) (`srt`) | 5,394 | Apache-2.0 | OS-level sandbox without containers | `srt "<cmd>"` uses sandbox-exec (macOS), bubblewrap (Linux) or WFP (Windows) plus HTTP/SOCKS proxies. `~/.srt-settings.json` holds `allowWrite: ["."]`, `denyRead`, and `allowedDomains: []`, which by default denies all network access. | Wrap the autonomous experiment loop's commands in `srt`, or enable Claude Code's built-in `sandbox` setting | Direct reuse (Apache-2.0) |
| 31 | [anthropics/claude-code-security-review](https://github.com/anthropics/claude-code-security-review) | 6,282 | MIT | Security-review GitHub Action | Diff-scoped security analysis with false-positive filtering | Judge's security check in CI | Direct reuse (MIT) |
| 32 | [e2b-dev/E2B](https://github.com/e2b-dev/E2B) | 14,034 | Apache-2.0 | Cloud sandboxes for agents | Firecracker microVM per agent via SDK (`Sandbox.create()`, `commands.run`) | Remote isolated workers or eval environments | Reuse (SDK) |
| 33 | [anthropics/claude-code](https://github.com/anthropics/claude-code) | 148,591 | No SPDX (proprietary terms) | Claude Code itself; the repo holds example hooks and plugins | `examples/hooks` (for example a bash command validator) and plugin examples | Canonical hook examples | Pattern |

### D. Evals and benchmarks
| # | Project | Stars | License | One-line | Mechanism to borrow | How it maps into Super-Skill | Adoption |
|---|---|---|---|---|---|---|---|
| 34 | [SWE-bench/SWE-bench](https://github.com/SWE-bench/SWE-bench) | 5,938 | MIT | Real GitHub-issue benchmark | Predictions JSONL `{instance_id, model_name_or_path, model_patch}` → `swebench eval verified -p preds --run-id X -j N` builds a Docker image per instance, applies the patch, and runs FAIL_TO_PASS and PASS_TO_PASS tests. Results are cached by (run_id, instance_id). | Super-Skill "patch mode" eval: 10 to 20 Lite instances with and without the skill | Direct reuse (MIT harness) |
| 35 | [SWE-agent/mini-swe-agent](https://github.com/SWE-agent/mini-swe-agent) | 8,097 | MIT | 100-line agent scoring over 74% on SWE-bench Verified | A minimal loop (bash-only actions, linear history), with `swebench infer` built on it | A baseline to compare against: shows whether 14 phases beat 100 lines | Reuse (MIT) |
| 36 | [SWE-agent/SWE-agent](https://github.com/SWE-agent/SWE-agent) | 20,448 | MIT | Issue-fixing agent | Agent-Computer Interface (custom commands with guarded editing and a linter on edit) | Post-edit lint hook idea | Pattern |
| 37 | [harbor-framework/harbor](https://github.com/harbor-framework/harbor) | 5,698 | Apache-2.0 | Official harness for Terminal-Bench 2.0 that evaluates arbitrary agents | A task is `task.toml` (agent/verifier timeouts; cpus/memory) + `instruction.md` + `tests/test.sh` + `solution/solve.sh`. Run it with `harbor run -d terminal-bench@2.0 -a claude-code -m anthropic/<model> --n-concurrent 4`, with an `--env daytona` option. It also ships SWE-bench and Aider Polyglot adapters. | **Best fit for proving Super-Skill works.** Write 10 to 20 "idea→product" tasks in Harbor format (each with a `test.sh` verifier) and run `claude-code` with vs without Super-Skill installed | Direct reuse (Apache-2.0) |
| 38 | [laude-institute/terminal-bench](https://github.com/laude-institute/terminal-bench) (now harbor-framework/terminal-bench-1) + [terminal-bench-2](https://github.com/laude-institute/terminal-bench-2) | 2,597 / 416 | Apache-2.0 | Terminal task benchmark | Dockerized tasks with test-based verification | Borrow task difficulty tiers | Reuse |
| 39 | [UKGovernmentBEIS/inspect_ai](https://github.com/UKGovernmentBEIS/inspect_ai) | 2,886 | MIT | UK AISI's eval framework | `@task` returns `Task(dataset, solver, scorer, sandbox="docker")`, with message, token and time limits. [meridianlabs-ai/inspect_swe](https://github.com/meridianlabs-ai/inspect_swe) (33 stars, MIT) wraps **Claude Code / Codex CLI as solvers**. Log viewer: `inspect view`. | Rigorous alternative to Harbor with a trajectory viewer | Reuse (MIT) |
| 40 | [UKGovernmentBEIS/inspect_evals](https://github.com/UKGovernmentBEIS/inspect_evals) | 684 | MIT | Community eval collection | Ready-made SWE-bench and other tasks for Inspect | Off-the-shelf datasets | Reuse |
| 41 | [promptfoo/promptfoo](https://github.com/promptfoo/promptfoo) | 25,567 | MIT | Declarative eval and red-team CLI | Provider `anthropic:claude-agent-sdk` (alias `anthropic:claude-code`) with config `working_dir`, `append_allowed_tools`, `permission_mode`, `max_turns`, `max_budget_usd`. Assertions include `javascript` (inspect `metadata.toolCalls`), `cost` (lessThan), `latency`, `llm-rubric`, `contains`, `skill-used` and `trace-span-count`. | `evals/promptfooconfig.yaml`: prompt = an idea, with asserts that the skill was used, that cost is under $X, and that a rubric judges the phase artifacts. Red-team mode tests the guardrails. | Direct reuse (MIT) |
| 42 | [openai/evals](https://github.com/openai/evals) | 19,524 | MIT | Eval framework plus registry | YAML registry of evals, with model-graded templates | Registry idea for Super-Skill eval cases | Pattern (maintenance mode) |
| 43 | [Aider-AI/polyglot-benchmark](https://github.com/Aider-AI/polyglot-benchmark) (+ [Aider-AI/aider](https://github.com/Aider-AI/aider) 49,284 stars, Apache-2.0) | 224 | No license (benchmark repo) | 225 Exercism problems in six languages | Pass@2 protocol: the agent sees test failures once and retries | "Retry once with test output" rule in the verification gate; available via the Harbor adapter | Pattern |
| 44 | [TheAgentCompany/TheAgentCompany](https://github.com/TheAgentCompany/TheAgentCompany) | 787 | MIT | Simulated software-company tasks | Checkpoint-based partial-credit scoring | Partial credit per phase (idea → PRD → code → deploy) | Pattern |
| 45 | [openai/SWELancer-Benchmark](https://github.com/openai/SWELancer-Benchmark) | 1,429 | No license | Freelance-task benchmark priced in dollars | Scores results by economic value, with E2E tests | "Product value" metric idea | Pattern |

### E. Observability, usage and cost
| # | Project | Stars | License | One-line | Mechanism to borrow | How it maps into Super-Skill | Adoption |
|---|---|---|---|---|---|---|---|
| 46 | [disler/claude-code-hooks-multi-agent-observability](https://github.com/disler/claude-code-hooks-multi-agent-observability) | 1,544 | **No license** | Real-time dashboard of hook events | Every event gets a second hook, `send_event.py --source-app X --event-type Y [--summarize]`, which POSTs `{source_app, session_id, hook_event_type, payload, model}` to `localhost:4000/events` with a 5 s timeout. A Bun server stores events in SQLite and streams them over WebSocket to a Vue UI, with swim lanes per session. | `log_event.py` appends the same schema to `.super-skill/events.jsonl` (and optionally POSTs). This is what makes "observability" real. | Pattern (no license) |
| 47 | [ryoppippi/ccusage](https://github.com/ryoppippi/ccusage) (now ccusage/ccusage) | 18,808 | MIT (LICENSE file; GitHub shows NOASSERTION) | Usage and cost from local JSONL | Scans `~/.claude/projects/**/*.jsonl` and `~/.config/claude/projects` (overridable with comma-separated `CLAUDE_CONFIG_DIR`), including subagent transcripts. Sums `usage.input_tokens + output_tokens + cache_creation + cache_read_input_tokens`. **Deduplicates by (message id, requestId).** Prices from a models.dev pricing table. Reports daily, session and 5-hour blocks. | Budget enforcement: a `PostToolUse`/`Stop` hook calls `npx ccusage session --json` (or parses `transcript_path` itself) and blocks or warns past `SUPER_SKILL_BUDGET_USD` | Direct reuse (MIT CLI) |
| 48 | [Maciek-roboblog/Claude-Code-Usage-Monitor](https://github.com/Maciek-roboblog/Claude-Code-Usage-Monitor) | 8,731 | MIT | Real-time usage monitor with predictions | Burn-rate plus P90 of the last 192 h of sessions to auto-detect limits, and predicts when the limit is reached | "Will this phase exceed the budget?" warning | Pattern / Reuse |
| 49 | [chiphuyen/sniffly](https://github.com/chiphuyen/sniffly) | 1,273 | MIT | Claude Code dashboard with error analysis | Parses logs to classify errors (for example "content not found", tool failures) and shows usage stats | Post-run retrospective from real data, not prose | Pattern / Reuse |
| 50 | [ColeMurray/claude-code-otel](https://github.com/ColeMurray/claude-code-otel) | 507 | MIT | OTel Collector, Prometheus, Loki and Grafana stack for Claude Code | Uses Claude Code's native OTel export (see 3.4) with prebuilt dashboards | Team-level observability recipe | Reuse (MIT compose files) |
| 51 | [langfuse/langfuse](https://github.com/langfuse/langfuse) | 35,210 | MIT core + separately licensed `ee/` | Open agent tracing and evals | Traces, spans and scores, LLM-as-judge evaluators, datasets | Optional trace sink (it can receive OTel) | Reuse (MIT core, self-hosted) |
| 52 | [Arize-ai/phoenix](https://github.com/Arize-ai/phoenix) | 11,654 | **Elastic License 2.0** | OTel-native tracing and evals | OpenInference span conventions, eval templates | Trace sink / eval UI | Use as a tool, but don't redistribute it as a hosted service (ELv2) |
| 53 | [comet-ml/opik](https://github.com/comet-ml/opik) | 22,295 | Apache-2.0 | Tracing, evals, dashboards | `@track` decorator, experiment comparison | Alternative sink | Reuse |
| 54 | [AgentOps-AI/agentops](https://github.com/AgentOps-AI/agentops) | 5,848 | MIT | Agent monitoring and cost SDK | Session replay, cost per session | Pattern | Pattern |
| 55 | [Helicone/helicone](https://github.com/Helicone/helicone) | 6,188 | Apache-2.0 | LLM observability proxy | Gateway-level logging and caching | Pattern | Pattern |
| 56 | [davila7/claude-code-templates](https://github.com/davila7/claude-code-templates) | 32,182 | MIT | CLI of Claude Code agents, commands, hooks and settings, plus analytics | Installable catalog (`npx claude-code-templates --hook ...`) and a local analytics dashboard | Distribute Super-Skill's hooks and settings as installable components | Reuse / Pattern |

Also verified but less central: [wshobson/agents](https://github.com/wshobson/agents) (40,095 stars, MIT; multi-harness plugin marketplace), [siteboon/claudecodeui](https://github.com/siteboon/claudecodeui) (13,862 stars, AGPL-3.0; web and mobile UI for sessions), [eyaltoledano/claude-task-master](https://github.com/eyaltoledano/claude-task-master) (28,113 stars, NOASSERTION; PRD→task graph), [disler/infinite-agentic-loop](https://github.com/disler/infinite-agentic-loop) (617 stars, no license; parallel sub-agent waves), [severity1/claude-code-auto-memory](https://github.com/severity1/claude-code-auto-memory) (158 stars, MIT; a PostToolUse hook tracks changed files and a Stop hook updates CLAUDE.md), and [hesreallyhim/awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code) (54,813 stars, CC-BY-NC-ND; discovery list, don't copy from it).

---

## 3. First-party Claude Code capabilities to use instead of reinventing them (docs checked 2026-09-30)

1. **`claude plugin eval`** (v2.1.269+, docs: code.claude.com/docs/en/plugin-evals). This is the most direct answer to "no eval harness". Each case lives at `evals/<case>/prompt.md`, whose frontmatter sets `max_turns`, `allowed_tools`, `timeout_seconds` and `model`, and whose body is the user prompt. Graders go in `graders/*.md` with `type:` set to one of `regex`, `tool_used`, `tool_order`, `file_exists`, `llm` or `baseline`, plus optional `weight` and `arm` fields. Each case runs 3 times **with the plugin and 3 times without it**, and the report shows WITH, W/OUT, Δ and COST. Useful flags: `--threshold` (exits 1 below the threshold, for CI), `--ablation none` and `--judge-model sonnet`. It works on skills-directory plugins too. Example skill-fired grader:
   ```markdown
   ---
   type: tool_used
   tool: Skill
   input_match: '"skill"\s*:\s*"(?:[\w-]+:)?super-skill"'
   ---
   ```
   The skill-creator plugin has a similar but separate `evals/evals.json` format.
2. **Worktrees:** `claude -w <name>` creates `.claude/worktrees/<name>/` on branch `worktree-<name>`, and `--tmux` opens it in tmux. A `.worktreeinclude` file copies gitignored files such as `.env` into each worktree. **A subagent with `isolation: worktree` in its frontmatter** gets its own worktree, and Claude Code enforces it: commands that resolve to the main checkout fail. Subagent frontmatter also supports `maxTurns`, `tools`, `disallowedTools`, `permissionMode`, `hooks`, `model` and `background`. This makes Planner-Worker-Judge implementable today as `.claude/agents/worker.md` with `isolation: worktree` and `judge.md` with read-only `tools`.
3. **Agent teams** (experimental; enable with `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`; interactive sessions only). A lead plus teammates share a task list and message each other. The `TaskCreated`, `TaskCompleted` and `TeammateIdle` hooks provide quality gates.
4. **Budget and turn caps in headless mode:** `claude -p --max-budget-usd 5.00 --max-turns 30 --output-format stream-json --json-schema '{...}'`. Subagent spend counts toward the cap, and once it is reached, new subagents fail with `Budget limit reached`. Other headless flags: `--permission-prompts none` (unattended runs), `--restricted` (eval harness on a shared machine), `--bare` and `--include-hook-events`.
5. **Native OpenTelemetry:** `CLAUDE_CODE_ENABLE_TELEMETRY=1`, `OTEL_METRICS_EXPORTER=otlp` and `OTEL_LOGS_EXPORTER=otlp`, plus `OTEL_EXPORTER_OTLP_ENDPOINT`. Metrics include `claude_code.cost.usage`, `claude_code.token.usage`, `claude_code.lines_of_code.count` and `claude_code.active_time.total`. Events include `claude_code.tool_result`, `claude_code.api_request`, `claude_code.skill_activated` and `claude_code.hook_execution_start`. These can be set in the `env` block of settings.json.
6. **Built-in Bash sandbox:** the `sandbox` settings (`enabled`, `excludedCommands`, `allowUnsandboxedCommands: false`, `network.allowedDomains`) are also exposed in the Agent SDK as `SandboxSettings`. They are backed by sandbox-runtime (#30).

---

## 4. Top 8 mechanisms to adopt, in priority order

1. **Fix the hooks with the correct schema and one stdin-JSON Python script per event** (pattern from hooks-mastery #25, SDK from cchooks #27). Use the example config in section 1.6: SessionStart context injection, PreToolUse deny via `permissionDecision`, a Stop verification gate that checks `stop_hook_active`, and PreCompact handoffs. Add a `scripts/test_hooks.py` that pipes sample payloads into each script and asserts on exit code and JSON, so the hooks are provably wired. Confirm with `claude doctor` and `--include-hook-events`.
2. **A real eval harness with a no-skill baseline:** `claude plugin eval` (section 3.1) for skill triggering and phase artifacts (Δ vs baseline, `--threshold` in CI via claude-code-action #13). Then Harbor (#37) with 10 to 20 "idea→working app" tasks, each having a `tests/test.sh` verifier, run as `harbor run -a claude-code` with vs without Super-Skill. Optionally add promptfoo's `cost` and `skill-used` assertions (#41).
3. **Parallel Workers as worktree-isolated subagents or processes:** `.claude/agents/worker.md` with `isolation: worktree` and `maxTurns`, plus a read-only `judge.md`. For fan-out outside a session, `scripts/fanout.py` uses the Agent SDK (#12) with `cwd=<worktree>` and `max_budget_usd`, and git-worktree lifecycle code modeled on claude-squad #1 (record the base commit, `remove -f`, then `prune`). Use best-of-N and a Judge merge as in Crystal #2.
4. **A dependency-DAG task board as the Planner's output** (beads #22 / vibe-kanban #3 / langgraph checkpointing #15). Store it in `.super-skill/tasks.jsonl` with `{id, phase, deps, status, owner_worktree}`. Workers pull only unblocked tasks, and the file-lock/claim protocol from agent-farm #8 prevents collisions.
5. **Budget enforcement in three layers:** hard caps via `--max-budget-usd` / `max_budget_usd` and `maxTurns` (section 3.4); a soft PostToolUse/Stop hook that sums the session's cost from `transcript_path` using ccusage's dedup rule of (message.id, requestId) (#47) and warns or blocks at thresholds; and burn-rate prediction as in Usage-Monitor #48. Optionally route cheap phases to cheaper models (claude-code-router #24, or per-subagent `model:`).
6. **Guardrails and sandboxing baseline:** `permissions.deny` for `.env`, `~/.ssh` and shell rc files, plus PreToolUse hooks that block `rm -rf`, force-push and pushes to main (trailofbits #28). Run the autonomous experiment loop inside the built-in sandbox or `srt` (#30), with `allowWrite: ["."]` and an explicit network allowlist, or container-use (#4) for full isolation. Run the security-review action (#31) in the Judge phase.
7. **Observability event stream:** one `log_event.py` attached to every event, which appends `{ts, source_app, session_id, agent_id, agent_type, hook_event_name, tool_name, summary}` to `.super-skill/events.jsonl` and optionally POSTs to a local dashboard (disler #46 pattern). Turn on native OTel (section 3.5) and point it at claude-code-otel #50 or Langfuse #51 for teams. Base the post-run retrospective on this data, with sniffly-style error classification (#49), instead of on prose.
8. **Context continuity through handoffs, replacing the prose memory systems:** a PreCompact/SessionEnd hook writes `handoff.yaml` (current phase, open tasks, decisions, failing tests), and a SessionStart hook with the `resume|compact` matcher re-injects it via `additionalContext` (Continuous-Claude #21). A Stop hook updates CLAUDE.md learnings (auto-memory pattern). Also measure it against the mini-swe-agent baseline (#35) to keep the 14-phase complexity honest.

### Licensing notes
- **Copy freely** (keep the license notice): MIT and Apache-2.0 projects, including ccusage, cchooks, claude-agent-sdk, claude-code-action, sandbox-runtime, container-use, SWE-bench, Harbor, inspect_ai, promptfoo, Continuous-Claude, beads and superpowers.
- **Pattern only, no code copying:**
  - No license: hooks-mastery, multi-agent-observability, trailofbits/claude-code-config, polyglot-benchmark and SWELancer.
  - AGPL: claude-squad and claudecodeui.
  - CC-BY-NC-ND: awesome-claude-code.
  - ELv2 (use as a tool only): Phoenix.
  - agent_farm's MIT license has a rider, so review it first.
- **Share-alike:** trailofbits/skills is CC-BY-SA, so reuse needs attribution and the same license.

### Unverified or caveats
- The hook field list comes from a model-summarized fetch of the live docs. Structure, event names, exit codes and decision fields are consistent with disler's working scripts, but newer fields (`if`, `args`, `once`, `defer`) should be re-checked against the docs before relying on them.
- The name of the PostToolUse result field is inconsistent between sources (`tool_result` vs `tool_response`), so parse both.
- Inspect's `token_limit`, `message_limit` and `time_limit` parameter names were not shown on the fetched page, so they are unconfirmed.
- Star counts are as of 2026-09-30.

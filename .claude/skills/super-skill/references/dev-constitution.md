# 开发宪法 — Development Constitution

> **Status**: non-negotiable. Extracted 2026-09-08 from the author's long-run Claude Code
> interaction records and delivered-project records — chiefly **We-AIPO** (290 commits /
> 126 modules / 218 tests / 78 deep optimizations / 11-of-11 unattended stages) and its
> `PROPOSAL_100x.md` methodology. A constitution article is not a guideline: **violation =
> stop and redo the phase**, not "preferably next time".
>
> Source transcript: `优化改进建议/AI开发项目全流程经验提炼与开发宪法更新指南_Transcript_2026-09-08.docx`.
>
> **Companion layers** (both 全局适配版, extracted from their projects 2026-09-07/08):
> [weaipo-constitution.md](weaipo-constitution.md) is the runtime constitution for
> unattended production systems (12 principles + 12 stop-on-sight violations + a
> conflict-adjudication order); [pai-station-doctrine.md](pai-station-doctrine.md) is
> the value/methodology adjudication layer (10+ project comparison, 难度=价值 density
> formula, opt-in iron law, kill-criteria milestones). This file is the proposal/
> research/plan core that binds them into the phase workflow.

## 序 — Why a constitution

An initial idea arrives bounded by the author's 认知/视野/经历 (cognition, vision,
experience) — it is timid by default ("初步想法可能没有这么大胆"). Every mechanism below
exists to push past that ceiling at the exact phase where the leverage is highest, and to
make the recurring hard-won rules of delivered projects impossible to forget. The
constitution binds the generator (plans, proposals, code) from above; the phase gates and
verifiers enforce it from below.

## 甲部 — 提案宪法 (Proposal Articles)

### C1 — 解决最难的问题 · Target the hardest problem
The proposal must target the **hardest real problem with genuine value** in its domain.
The hardest problems are the most worth solving — a truly solved hard problem is where
all the value lives. A "差不多的方案" (good-enough plan) or a comfortable pivot to an
easier problem is **unconstitutional at the proposal stage**. Do not fear the challenge.

### C2 — 大胆想象，天马行空合法 · Boldness is legal, timidity is not
At proposal time, imagination must be maximally open — even things previously considered
难以想象/难以实现 (unthinkable, infeasible) belong **in the proposal**. Constraints are
negotiated later, at architecture and WBS; the proposal itself must not be pre-shrunk.
The Idea Factory's ambiguity gate must never become a boldness gate.

### C3 — 世界最优且可落地 · World-best, and landable
After researching GitHub and the open network, the proposal's plan must be the **current
world-best implementable approach** — not the locally-known best, not the first workable
one. "最难实现" is acceptable; "不是最优" is not. Hard-to-implement has known breaking
points (decompose, prototype, iterate); suboptimal has none.

## 乙部 — 调研宪法 (Research Articles)

### C4 — 站在巨人肩膀上 · Stand on the shoulders of giants
Never build from scratch what the world already built well. Research first, find the
**top-tier existing work**, then build on it — cloning and adapting, even 缝合/粘贴/
复制/抄作业 (stitch, paste, copy, homework-copy; license permitting), is the correct and
highest-efficiency path. 从零造轮子 ("低级开发") is a constitutional violation: it wastes
the one resource a small team cannot buy back — time.

## 丙部 — 技术方案宪法 (Technical-Plan Articles)

### C5 — 当前条件下的最优解 · The optimal solution under actual constraints
Multiple technical routes will always look plausible. For **this** project's goal, under
**current** technical conditions and **this** environment, one of them is best — the plan
must be that one, and must record **why** (ADR: hard-to-reverse + surprising +
real-trade-off). "都能实现" is not a selection criterion; it is an abdication.

## 丁部 — 红线 (Red Lines — never cross)

| # | Red line | Enforcement |
|---|----------|-------------|
| **R1** | **代理用完即关** — after pushing to GitHub / using the Clash proxy, restore the network (direct mode, no TUN/DNS residue). Never leave the machine proxied. | `clash-proxy` `push` closes by default; `stop()` switches direct via API first |
| **R2** | **禁止静默失败** — no silent `except: pass`. Failures surface or the run stops. (We-AIPO: 163 swallowed errors once hid every real problem; cleanup was optimization S2) | review + `verification-gate`; We-AIPO case study |
| **R3** | **根因先于修复** — name the exact root cause and rule out the wrong hypothesis before touching code | `systematic-debugging` Phase 0 red-first; Iceberg Rule |
| **R4** | **穷尽之前不许说"做不到"** — "I can't" without evidence of exhausted options (L1–L4 escalation) is refused | `high-agency` anti-rationalization table |
| **R5** | **验证者 > 生成者** — when output stalls, strengthen the verifier, not the generator | Phase 10 Ralph Loop; `upgrade_audit` pattern |
| **R6** | **安全检查先于 commit** — no hardcoded secrets, inputs validated, scan before every push | standing security rules; secret scans in CI |

## 戊部 — Enforcement map (article → phase gate)

| Article | Gate that enforces it |
|---------|----------------------|
| C1 hardest problem | Idea Factory `proposal-forge` **ten× delta index** — falsifiable 10× gate kills incremental ideas; scorecard verdict gate |
| C2 boldness | Phase 0 Visionary Elevation (anti-consensus design) + idea-intake must not pre-shrink |
| C3 world-best & landable | Phase 2 GitHub Discovery + research-orchestrator gap analysis before the Proposal Approval Gate |
| C4 giants' shoulders | Phase 2: score ≥80% → **clone and adapt** is the default; building from scratch requires a documented miss (<60%) |
| C5 optimal solution | Phase 5 architecture + ADR discipline (3-part test) |
| R1–R6 | Phase 9/10 verification + hooks + the tooling listed above |

## 己部 — Evidence (where each article proved itself)

- **C1/C3** — We-AIPO `PROPOSAL_100x.md`: the accepted proposal was a 5-dimension ×
  20-item 100× rebuild, not an incremental patch — and it landed (78 optimizations,
  11/11 unattended stages). The 10×-gate pattern generalizes it.
- **C4** — We-AIPO itself was built by porting ResearchFactory-Eng's orchestration
  architecture; Super-Skill integrates 8 external skill systems (OpenWolf, mattpocock,
  cc-harness, …) instead of rewriting them. This document is also standing on one.
- **C5** — We-AIPO's tech-route decisions recorded per-round in `PROPOSAL_ROUND3-7.md`
  (each round: current options → chosen → why → evidence).
- **R1** — the 2026-08 push failures ("Clash 退出后 git push 走死代理") are the exact
  incident class R1 exists for; V4.1.6's API-first `push` command is the codified fix.
- **R2** — We-AIPO optimization S2 (`except:pass 全面清理`, 163 sites): silent failure
  was the single largest debugging-time multiplier.

## Review

The constitution is re-examined whenever a delivered project completes (Phase 12
post-run evolution): new red lines earned the hard way get proposed as amendments with
evidence, then versioned here.

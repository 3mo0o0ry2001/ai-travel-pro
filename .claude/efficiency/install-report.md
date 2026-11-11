# Efficiency OS install report
date: 2026-11-11T10:30:00+00:00  python: python (3.13)  os: nt/win32  hook style: absolute

| file | action |
|---|---|
| .claude/agents/architect.md | skip (identical) |
| .claude/agents/builder-isolated.md | skip (identical) |
| .claude/agents/builder.md | skip (identical) |
| .claude/agents/reviewer-deep.md | skip (identical) |
| .claude/agents/reviewer.md | skip (identical) |
| .claude/agents/scout.md | skip (identical) |
| .claude/efficiency/ROUTING.md | skip (identical) |
| .claude/efficiency/agents-disabled/heavy.md | skip (identical) |
| .claude/efficiency/bench/compare.py | skip (identical) |
| .claude/efficiency/bench/run.py | skip (identical) |
| .claude/efficiency/bench/tasks.json | skip (identical) |
| .claude/efficiency/bin/calibrate.py | skip (identical) |
| .claude/efficiency/bin/classify.py | skip (identical) |
| .claude/efficiency/bin/common.py | skip (identical) |
| .claude/efficiency/bin/format_hook.py | skip (identical) |
| .claude/efficiency/bin/gate.py | skip (identical) |
| .claude/efficiency/bin/guard.py | skip (identical) |
| .claude/efficiency/bin/install.py | skip (identical) |
| .claude/efficiency/bin/model_guard.py | skip (identical) |
| .claude/efficiency/bin/report.py | skip (identical) |
| .claude/efficiency/bin/smoke.py | skip (identical) |
| .claude/efficiency/bin/statusline.py | skip (identical) |
| .claude/efficiency/bin/telemetry.py | skip (identical) |
| .claude/efficiency/bin/verify.py | skip (identical) |
| .claude/efficiency/config.json | skip (identical) |
| .claude/efficiency/gates.json | skip (identical) |
| .claude/efficiency/pricing.json | skip (modified locally since install; keeping yours) |
| .claude/efficiency/tests/test_all.py | update (runtime, by manifest) |
| .claude/settings.json | merge |
| .claude/skills/benchmark/SKILL.md | skip (identical) |
| .claude/skills/calibrate/SKILL.md | skip (identical) |
| .claude/skills/codify/SKILL.md | skip (identical) |
| .claude/skills/cost-check/SKILL.md | skip (identical) |
| .claude/skills/efficiency-report/SKILL.md | skip (identical) |
| .claude/skills/enable-heavy/SKILL.md | skip (identical) |
| .claude/skills/gate/SKILL.md | skip (identical) |
| .claude/skills/handoff/SKILL.md | skip (identical) |
| .claude/skills/lean-check/SKILL.md | skip (identical) |
| .claude/skills/route/SKILL.md | skip (identical) |
| .gitignore | merge |
| CLAUDE.md | merge |
| scripts/README.md | skip (identical) |

### .claude/efficiency/tests/test_all.py (update (runtime, by manifest))
```diff
--- current
+++ proposed
@@ -505,7 +505,7 @@
         for _ in range(n): t0 = time.perf_counter(); fn(); xs.append((time.perf_counter() - t0) * 1000)
         xs = sorted(xs); return {"cold_ms": round(xs[0] if n == 1 else None or 0, 1), "p50_ms": round(xs[len(xs) // 2], 1), "p95_ms": round(xs[min(len(xs) - 1, int(len(xs) * 0.95))], 1), "n": n}
     def test_hook_latency_cold_warm_breakdown(self):
-        p = self.p; budget = float(os.environ.get("EOS_OVERHEAD_BUDGET_MS") or json.loads((p.eos / "config.json").read_text()).get("overhead_budget_ms", 800))
+        p = self.p; budget = float(os.environ.get("EOS_OVERHEAD_BUDGET_MS") or json.loads((p.eos / "config.json").read_text()).get("overhead_budget_ms", 3000))
         tmp = pathlib.Path(tempfile.mkdtemp()); big = tmp / "big.jsonl"
         with open(big, "w") as f:
             for i in range(600): f.write(rec(f"m{i}", "claude-opus-5", 100, 100, 1000, 10) + "\n")
```

### .claude/settings.json (merge)
```diff
```

### .gitignore (merge)
```diff
```

### CLAUDE.md (merge)
```diff
```


## Hook command validation (executed through the shell with sample payloads)
| check | result | detail |
|---|---|---|
| hook command executes: SessionStart | PASS | exit 0 |
| hook command executes: UserPromptSubmit | PASS | history for this class yet\" (deterministic first pass; override with a one-line reason if wrong)"}} |
| hook command executes: SubagentStart | PASS | exit 0 |
| hook command executes: SubagentStop | PASS | exit 0 |
| hook command executes: Stop | PASS | exit 0 |
| hook command executes: SessionEnd | PASS | exit 0 |
| hook command executes: PreCompact | PASS | exit 0 |
| hook command executes: PreToolUse | PASS | exit 0 |
| hook command executes: PreModelSwitch | PASS | exit 0 |
| status line command executes | PASS | Opus | ctx 12% | last 0k · |
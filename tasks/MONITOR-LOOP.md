# Monitor Loop — Supervisor Role
**Last Run**: 2026-05-05 17:53
**Frequency**: Every 2 minutes (manual or cron trigger)

---

## My Role

```
[Execution AI] ──writes code──► [Me: Review] ──optimize──► [OPGG Study] ──next tasks──► [Execution AI]
                                           ▲                                          │
                                           └──────────── feedback loop ─────────────────┘
```

1. **Review** what execution AI committed/updated
2. **Optimize** — improve their code quality
3. **Study OPGG** — each round, check OPGG for new insights
4. **Write next tasks** — keep pipeline full
5. **Ensure no blockage** — if blocked, resolve immediately

---

## Monitor Checklist (Every Round)

### Review Phase
- [ ] Read execution AI's latest file changes
- [ ] Check TASK-02/TASK-03 status
- [ ] Verify code quality: no console.log, proper types, dark theme compliance
- [ ] Flag any bugs or edge cases
- [ ] If done → unblock next task

### OPGG Study Phase
- [ ] Search OPGG for latest rune page layout/fields
- [ ] Compare against current TASK-01 spec
- [ ] If new findings → update TASK-01 and add to task queue

### Task Update Phase
- [ ] Update INDEX.md progress bars
- [ ] Write next task if pipeline is running low
- [ ] If all tasks done → create optimization task
- [ ] Log in ## Progress Log

---

## Current Status (as of 2026-05-05 17:53)

| Task | Status | Last Update |
|------|--------|------------|
| TASK-01 | ✅ DONE | 17:42 |
| TASK-02 | 🔄 IN PROGRESS | Execution AI working |
| TASK-03 | ⏳ TODO | Blocked by 02 |

---

## Key Metrics to Watch

1. **Execution AI blocked?** → Unblock immediately (answer questions, clarify tasks)
2. **Task file outdated?** → Update with latest OPGG findings
3. **New OPGG data?** → Add to TASK-01, create follow-up task
4. **Performance issue found?** → Add to TASK-03 or create TASK-04

---

## Escalation Rules

- **Execution AI asks question** → Answer in INDEX.md or directly
- **Found blocker in dependencies** → Document and work around
- **OPGG changed significantly** → Update all task files + notify execution AI
- **Everything done** → Create TASK-04 (optimization pass) to keep pipeline alive

---

## Progress Log

```
## Progress Log
- [2026-05-05 17:42] [SETUP] Created all task files, set up cron job
- [2026-05-05 17:53] [ROLE] Clarified monitor loop — I review, optimize, study OPGG, write next tasks
```

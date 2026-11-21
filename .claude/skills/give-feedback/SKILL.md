---
name: give-feedback
description: Analyze a completed running session (splits, pace, heart rate, RPE, and soreness/injury notes) against the planned workout and provide recovery and next-session adjustments.
---

# Post-Session Feedback Skill

1. **Parse the Session**: Run or reference `stridecoach/coach_api.py` (or the Stage 2 structured parser) on the workout log.
2. **Evaluate Execution**:
   - Check pace consistency (positive vs. negative split) and cardiac drift (HR climbing at steady pace).
   - Compare actual RPE and pace against the intended training zone.
3. **Injury & Load Triage**:
   - If the athlete reports sharp/localized pain (e.g., Achilles twinge, shin pain), recommend modifying or replacing the next quality session with easy cross-training or rest.
4. **Format**: Give 3 concise bullets: (1) Execution summary, (2) Physiological/load takeaway, (3) Actionable adjustment for the next 48 hours.

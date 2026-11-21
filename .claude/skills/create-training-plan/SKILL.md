---
name: create-training-plan
description: Generate a periodized multi-week running plan (5K, 10K, Half Marathon, Marathon) from the athlete's goal race, current weekly volume, and recent race PB. Use when the user asks to build or adapt a training plan.
---

# Create Training Plan Skill

1. **Gather Inputs**: Confirm goal distance, target race date/time, current weekly mileage (km), and longest recent run.
2. **Calculate Paces**: Derive Easy (E), Marathon (M), Threshold (T), Interval (I), and Repetition (R) paces using Jack Daniels' VDOT methodology.
3. **Apply Safe Progression Rules**:
   - Increase weekly volume by at most 10% per week.
   - Insert a cutback/recovery week (-20% to -25% volume) every 4th week.
   - Keep quality (hard) sessions to at most 20% of weekly mileage (80/20 polarized rule).
4. **Output Structure**: Present a week-by-week table with total km, key workouts, and long run distance.

# Executive Summary: Recommendation Rollout Engagement Collapse

## Business Question

Did the recommendation model rollout on `2025-11-17` create a localized engagement collapse?

## Key Findings

- Affected regions: `IN-North, IN-South`.
- Primary metric: `plays_per_active_user`.
- Affected-region engagement moved from `5.62` plays/user pre-rollout to `4.14` post-rollout.
- Affected-region change: `-26.3%`.
- Unaffected-region change: `-1.4%`.
- Difference-in-differences estimate: `-1.396` plays/user.
- Bootstrap 95% CI for affected post-minus-pre: `[-0.314, -0.261]`.
- Estimated affected-region loss: `886` video plays and `107.3` watch hours.

## Interpretation

The evidence supports a rollout-related degradation in the affected regions. The drop is visible in the primary engagement metric, funnel health, and post-rollout anomaly flags.

## Recommendation

Evidence supports rolling back v4.2 in IN-North and IN-South, then auditing ranking diversity and feature drift before re-launch.

## Limitations

This is a deterministic synthetic case study. It demonstrates product analytics methodology, not a real production incident. The analysis is observational and should not be described as proof from a randomized experiment.

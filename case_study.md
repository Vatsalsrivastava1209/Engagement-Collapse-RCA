# Case Study: Recommendation Model Rollout RCA

## Problem

A streaming product observes an engagement drop after a recommendation model update. The business needs to know whether the issue is global, localized, or unrelated to the rollout.

## Hypothesis

The `v4.2` recommendation model degraded engagement in the rollout regions, `IN-North` and `IN-South`, after `2025-11-17`.

## Data

The project uses deterministic synthetic clickstream events with session, region, device, app-version, model-version, content, and funnel metadata. The data is synthetic by design; it is used to demonstrate reproducible RCA methodology.

## Methodology

1. Validate event schema, timestamp parsing, unique event IDs, rollout assignment, and session ordering.
2. Use SQL to build a pre/post metric tree for affected and unaffected cohorts.
3. Segment engagement by region, device, app version, and model version.
4. Analyze funnel health from app open to impression to play to completion.
5. Flag anomalies against the pre-rollout baseline.
6. Quantify lost plays and lost watch hours.

## Findings

- Affected-region plays per active user dropped from `5.62` to `4.14`.
- Affected-region change was `-26.3%`; unaffected-region change was `-1.4%`.
- Bounce rate in affected regions rose from `7.6%` to `32.0%`.
- Completion rate in affected regions fell from `64.4%` to `38.1%`.
- Estimated loss was `886` video plays and `107.3` watch hours.

## Recommendation

Rollback model `v4.2` in `IN-North` and `IN-South`. Before relaunch, audit model-ranking diversity, content-category mix, and feature drift. Relaunch through a canary with automated alerts on plays per active user, bounce rate, completion rate, and watch hours.

## Limitations

This is a synthetic, observational RCA case study. It supports a rollout-related degradation story, but it should not be described as randomized causal proof.

## Next Steps

- Add real-time alert thresholds.
- Add content-category mix diagnostics.
- Add experiment guardrails before future model rollouts.
- Add monitoring views for model version, region, and device combinations.

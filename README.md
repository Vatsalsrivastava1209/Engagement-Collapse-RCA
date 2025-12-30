# Case Study: Investigating an Engagement Collapse After a Recommendation Model Update

## Executive Summary & Key Findings

This project utilized PostgreSQL, Python (Pandas, Seaborn), and advanced SQL (Window Functions, CTEs) to perform a **Root Cause Analysis (RCA)** on a severe metric collapse.

| Metric | Impact | Root Cause | Business Impact |
| :--- | :--- | :--- | :--- |
| **Overall Watch Time** | **17% Collapse** | Localized failure in **Recommendation Model v4.2** | Loss of approximately **[INSERT FINAL LOST PLAYS HERE]** total video plays across two key regions over 7 days. |
| **Location** | **Highly Segmented** | Failure traced specifically to the **IN-North and IN-South regions**. | High user frustration confirmed by a **[INSERT BOUNCE RATE SPIKE %]** spike in Bounce Rate in affected areas. |

***

## Technology Stack & Techniques

* **Database:** PostgreSQL (Primary analytics platform, used for DDL/DML and complex joins).
* **Tools:** Python, Pandas, Matplotlib, **Seaborn** (Visualization), `psycopg2` (ETL).
* **SQL Mastery:** Employed **Common Table Expressions (CTEs)** for clear multi-step logic, **Window Functions** for session-level analysis (implied), and **Defensive SQL (`NULLIF`)** to prevent query failure.
* **Techniques:** Segmented Root Cause Analysis, Time-Series Breakdown, and Behavioral Proxy Analysis (Bounce Rate).

***

## Phase I & II: Diagnosis and Evidence

The investigation followed a clear Hypothesis Tree, ruling out global factors (e.g., device type, app version) to isolate the segment responsible for the collapse.

### 1. Initial Observation and Segmentation (The "Where")

Segmented time-series analysis was the key diagnostic step.

* **Finding:** The decline in Average Daily Plays per User was overwhelmingly concentrated in **IN-North and IN-South**, immediately isolating the scope of the problem to a failure in regional content delivery.
* **Visualization:** Segmented Line Plot of Average Daily Plays per User.



### 2. Behavioral Analysis Confirms Failure (The "Why")

Analyzing the **Bounce Rate Proxy** confirmed the behavioral cause—users were leaving the app immediately due to poor content recommendations.

* **Finding:** The bounce rate for IN-North/South **spiked sharply** after November 17, confirming the failure mechanism: the model served unengaging content, causing instant abandonment.
* **Visualization:** Segmented Line Plot of Daily Bounce Rate Proxy (Users who Opened but Did Not Play).



### 3. Final Quantification (The "Cost")

By using the pre-drop period (Baseline) to establish expected performance, the total loss was quantified for executive reporting.

| Metric | Value |
| :--- | :--- |
| **Baseline Avg Plays/User (Affected Regions)** | $\approx [BASELINE AVG PLAYS]$ |
| **Post-Drop Avg Plays/User (Affected Regions)** | $\approx [POST-DROP AVG PLAYS]$ |
| **Total Plays Lost (Nov 17 - Nov 23)** | **[INSERT FINAL LOST PLAYS HERE]** |

***

## Actionable Recommendations

This analysis delivered a clear, prioritized action plan to stop the metric bleeding and prevent future recurrence.

| Priority | Stakeholder | Recommendation | Monitoring KPI |
| :--- | :--- | :--- | :--- |
| **P1: Immediate Stop** | Engineering | **Rollback Recommendation Model v4.2** for all users in **IN-North and IN-South** to the stable v4.1 model immediately. | IN-North/South **Bounce Rate** must fall below 12% within **48 hours**. |
| **P2: Deep Investigation** | Data Science | **Audit Model v4.2 Feature Drift:** Investigate the training data and feature importance to find why the model failed to generalize to user preferences in the affected regions. | Check if model v4.2's output diversity score dropped for the affected regions. |
| **P3: Prevention** | Product/Ops | Implement a mandatory **Canary Testing** phase for all major model updates, limited to low-impact regions, with automated metric alerts. | Zero critical metric drops within 90 days post-launch. |

***

## Repository Structure

* `./data_generator.py`: Python script used to create the synthetic JSONL clickstream data.
* `./engagement_logs/`: Directory containing the `day_*.json` event logs.
* `./analysis_notebook.ipynb`: The Jupyter Notebook containing all the connection code, advanced SQL queries, Pandas manipulation, and visualization code.
* `./sql_queries.sql`: Clean file containing the DDL (`CREATE TABLE`, `CREATE INDEX`) and the final RCA queries used.

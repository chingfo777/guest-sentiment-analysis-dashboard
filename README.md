# Guest Sentiment Analysis Dashboard

**Objective:** Analyze guest review text to score sentiment by department,
surface recurring complaint themes, and track sentiment trends over time to
support service-quality decisions.

**Tools:** Python (Pandas), SQL (SQLite), Matplotlib, Excel (openpyxl)

> **Note on scope:** Your original CV bullet under this title described an
> *inventory/procurement re-order point* project, which didn't match the
> "Guest Sentiment Analysis" name. I built the project to match the **title**
> since sentiment analysis is the more relevant, differentiated skill for a
> hospitality data role — let me know if you'd actually prefer the inventory
> version built instead, I can do that too.

## What the script does
1. **Generates 600 synthetic guest reviews** across 5 departments (Front
   Desk, Housekeeping, F&B, Spa, Concierge) with realistic positive/neutral/
   negative language — `guest_reviews_2024.csv`.
2. **Scores sentiment** using a custom hospitality-domain lexicon (no
   internet/model download required — fully transparent, tunable word list)
   producing a score from -1 (negative) to +1 (positive) per review.
3. **Loads reviews into SQLite** and runs **SQL aggregation queries**:
   average sentiment/rating by department, and monthly sentiment trend.
4. **Extracts top recurring keywords in negative reviews** — a root-cause
   signal for service teams (e.g. "wait", "cold", "restocked").
5. **Exports a multi-sheet Excel workbook** (`Guest_Sentiment_Dashboard.xlsx`)
   with department summary, monthly trend, keyword frequency, and raw scored
   data — ready to hand to an ops manager.
6. **Builds 4 dashboard charts**: sentiment by department, overall sentiment
   split, monthly trend line, and top complaint keywords.

## Files
| File | Description |
|---|---|
| `guest_reviews_scored.csv` | All reviews with sentiment score + label |
| `outputs/department_summary.csv` | SQL: sentiment/rating aggregated by dept |
| `outputs/monthly_sentiment_trend.csv` | SQL: sentiment trend by month |
| `outputs/top_negative_keywords.csv` | Most frequent words in negative reviews |
| `outputs/Guest_Sentiment_Dashboard.xlsx` | Multi-sheet Excel dashboard export |
| `outputs/01_sentiment_by_department.png` | Sentiment score per department |
| `outputs/02_overall_sentiment_distribution.png` | Pos/Neu/Neg split |
| `outputs/03_monthly_sentiment_trend.png` | Sentiment over time |
| `outputs/04_top_negative_keywords.png` | Complaint keyword frequency |

## How to run
```bash
python3 sentiment_dashboard.py
```

## Note on the data
This is **synthetic review data generated for demonstration purposes**. The
sentiment-scoring logic (`score_sentiment()`) and SQL queries are written to
work identically on a real guest-review export (e.g. from a review-aggregation
tool or PMS) — just swap the CSV source.

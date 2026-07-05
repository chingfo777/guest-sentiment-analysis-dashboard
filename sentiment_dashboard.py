"""
Guest Sentiment Analysis Dashboard
------------------------------------
Objective: Analyze guest review text to score sentiment per department,
surface recurring complaint/praise themes, and track sentiment trends over
time to support service-quality decisions.

Tools: Python (Pandas), SQL (SQLite), Matplotlib, Excel (openpyxl export)
Author: Subha Shil (project build)

Note: Sentiment scoring uses a custom hospitality-domain lexicon (no external
downloads required) rather than a pre-trained NLTK/VADER corpus, since this
environment has no internet access. The approach is transparent and tunable.
"""

import sqlite3
import re
from collections import Counter

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

RNG = np.random.default_rng(7)

# ---------------------------------------------------------------------------
# 1. GENERATE SYNTHETIC GUEST REVIEW DATA
# ---------------------------------------------------------------------------
departments = ["Front Desk", "Housekeeping", "F&B / Restaurant", "Spa & Wellness", "Concierge"]

positive_snippets = [
    "The staff was incredibly friendly and helpful",
    "Room was spotless and beautifully maintained",
    "Check-in was fast and seamless",
    "Breakfast selection was excellent and fresh",
    "Concierge went above and beyond to help us",
    "Loved the attention to detail in the room",
    "Staff greeted us warmly every single day",
    "The spa treatment was relaxing and professional",
    "Quick response to our requests, very efficient",
    "Beautiful property, exceeded our expectations",
]

negative_snippets = [
    "Check-in took far too long and felt disorganized",
    "Room was not properly cleaned upon arrival",
    "Staff seemed inattentive and slow to respond",
    "Breakfast was cold and options were limited",
    "Requested items never arrived at our room",
    "Noise from the hallway disturbed our sleep",
    "Billing error took days to resolve",
    "Air conditioning was not working properly",
    "Long wait times at the restaurant",
    "Towels and toiletries were not restocked",
]

neutral_snippets = [
    "Stay was fine, nothing particularly memorable",
    "Average experience overall, met basic expectations",
    "Room was okay, standard hotel amenities",
    "Service was acceptable, no major issues",
    "Location was convenient, hotel was as described",
]


def build_review(sentiment_pool, dept):
    text = RNG.choice(sentiment_pool)
    extra = RNG.choice([
        "", " Would recommend to others.", " Will definitely consider staying again.",
        " Overall a decent trip.", " Thank you to the team.", ""
    ])
    return f"{text} regarding {dept.lower()}.{extra}"


def generate_reviews(n=600):
    rows = []
    dates = pd.date_range("2024-01-01", "2024-12-31", freq="D")
    for i in range(n):
        dept = RNG.choice(departments)
        # Weighted sentiment distribution: 55% positive, 25% neutral, 20% negative
        sentiment_choice = RNG.choice(["pos", "neu", "neg"], p=[0.55, 0.25, 0.20])
        if sentiment_choice == "pos":
            text = build_review(positive_snippets, dept)
            rating = RNG.integers(4, 6)
        elif sentiment_choice == "neg":
            text = build_review(negative_snippets, dept)
            rating = RNG.integers(1, 3)
        else:
            text = build_review(neutral_snippets, dept)
            rating = 3

        rows.append({
            "review_id": i + 1,
            "date": RNG.choice(dates),
            "department": dept,
            "rating": int(rating),
            "review_text": text,
        })
    df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    return df


reviews = generate_reviews()
reviews.to_csv("guest_reviews_2024.csv", index=False)
print(f"Generated {len(reviews)} guest reviews -> guest_reviews_2024.csv")

# ---------------------------------------------------------------------------
# 2. LEXICON-BASED SENTIMENT SCORING (custom hospitality word list)
# ---------------------------------------------------------------------------
POSITIVE_WORDS = {
    "friendly", "helpful", "spotless", "beautifully", "fast", "seamless",
    "excellent", "fresh", "warmly", "relaxing", "professional", "efficient",
    "beautiful", "exceeded", "recommend", "great", "clean", "quick", "amazing",
    "wonderful", "attentive", "loved", "thank",
}
NEGATIVE_WORDS = {
    "long", "disorganized", "not", "inattentive", "slow", "cold", "limited",
    "never", "disturbed", "error", "not working", "wait", "restocked",
    "noise", "issue", "issues", "poor", "delay", "dirty", "broken", "rude",
}


def score_sentiment(text: str) -> float:
    words = re.findall(r"[a-z]+", text.lower())
    pos_hits = sum(1 for w in words if w in POSITIVE_WORDS)
    neg_hits = sum(1 for w in words if w in NEGATIVE_WORDS)
    total = pos_hits + neg_hits
    if total == 0:
        return 0.0
    return round((pos_hits - neg_hits) / total, 3)  # range -1 (neg) to +1 (pos)


def classify(score: float) -> str:
    if score > 0.15:
        return "Positive"
    elif score < -0.15:
        return "Negative"
    return "Neutral"


reviews["sentiment_score"] = reviews["review_text"].apply(score_sentiment)
reviews["sentiment_label"] = reviews["sentiment_score"].apply(classify)
reviews.to_csv("guest_reviews_scored.csv", index=False)

# ---------------------------------------------------------------------------
# 3. SQL LAYER: Load into SQLite and run aggregation queries
# ---------------------------------------------------------------------------
conn = sqlite3.connect(":memory:")
reviews.to_sql("reviews", conn, index=False, if_exists="replace")

dept_summary = pd.read_sql_query(
    """
    SELECT
        department,
        COUNT(*) AS total_reviews,
        ROUND(AVG(rating), 2) AS avg_rating,
        ROUND(AVG(sentiment_score), 3) AS avg_sentiment_score,
        SUM(CASE WHEN sentiment_label = 'Positive' THEN 1 ELSE 0 END) AS positive_count,
        SUM(CASE WHEN sentiment_label = 'Negative' THEN 1 ELSE 0 END) AS negative_count,
        SUM(CASE WHEN sentiment_label = 'Neutral' THEN 1 ELSE 0 END) AS neutral_count
    FROM reviews
    GROUP BY department
    ORDER BY avg_sentiment_score DESC;
    """,
    conn,
)

monthly_trend = pd.read_sql_query(
    """
    SELECT
        strftime('%Y-%m', date) AS month,
        ROUND(AVG(sentiment_score), 3) AS avg_sentiment_score,
        ROUND(AVG(rating), 2) AS avg_rating,
        COUNT(*) AS review_count
    FROM reviews
    GROUP BY month
    ORDER BY month;
    """,
    conn,
)

lowest_dept = dept_summary.sort_values("avg_sentiment_score").iloc[0]
print(f"\nDepartment needing most attention: {lowest_dept['department']} "
      f"(avg sentiment {lowest_dept['avg_sentiment_score']}, "
      f"{lowest_dept['negative_count']} negative reviews)")

dept_summary.to_csv("outputs/department_summary.csv", index=False)
monthly_trend.to_csv("outputs/monthly_sentiment_trend.csv", index=False)

# ---------------------------------------------------------------------------
# 4. TOP KEYWORDS IN NEGATIVE REVIEWS (root-cause signal)
# ---------------------------------------------------------------------------
STOPWORDS = {
    "the", "was", "our", "and", "a", "to", "of", "in", "for", "at", "regarding",
    "will", "would", "overall", "trip", "team", "others", "again", "considering",
    "consider", "front", "desk", "housekeeping", "restaurant", "spa", "wellness",
    "concierge",
}
neg_text = " ".join(reviews.loc[reviews["sentiment_label"] == "Negative", "review_text"])
words = [w for w in re.findall(r"[a-z]+", neg_text.lower()) if w not in STOPWORDS and len(w) > 3]
top_keywords = Counter(words).most_common(10)
keyword_df = pd.DataFrame(top_keywords, columns=["keyword", "frequency"])
keyword_df.to_csv("outputs/top_negative_keywords.csv", index=False)

# ---------------------------------------------------------------------------
# 5. EXCEL EXPORT (multi-sheet workbook, as referenced in CV skillset)
# ---------------------------------------------------------------------------
with pd.ExcelWriter("outputs/Guest_Sentiment_Dashboard.xlsx", engine="openpyxl") as writer:
    dept_summary.to_excel(writer, sheet_name="Department Summary", index=False)
    monthly_trend.to_excel(writer, sheet_name="Monthly Trend", index=False)
    keyword_df.to_excel(writer, sheet_name="Top Negative Keywords", index=False)
    reviews.to_excel(writer, sheet_name="Raw Scored Reviews", index=False)

# ---------------------------------------------------------------------------
# 6. DASHBOARD VISUALIZATIONS
# ---------------------------------------------------------------------------
plt.style.use("seaborn-v0_8-whitegrid")

# 6a. Average sentiment score by department
plt.figure(figsize=(9, 5))
colors = ["#2A9D8F" if s >= 0 else "#E63946" for s in dept_summary["avg_sentiment_score"]]
plt.barh(dept_summary["department"], dept_summary["avg_sentiment_score"], color=colors)
plt.axvline(0, color="black", linewidth=0.8)
plt.xlabel("Average Sentiment Score (-1 to +1)")
plt.title("Guest Sentiment by Department")
plt.tight_layout()
plt.savefig("outputs/01_sentiment_by_department.png", dpi=150)
plt.close()

# 6b. Sentiment distribution overall
sentiment_counts = reviews["sentiment_label"].value_counts()
plt.figure(figsize=(6, 6))
plt.pie(
    sentiment_counts,
    labels=sentiment_counts.index,
    autopct="%1.1f%%",
    colors=["#2A9D8F", "#F4A261", "#E63946"],
)
plt.title("Overall Sentiment Distribution (2024)")
plt.tight_layout()
plt.savefig("outputs/02_overall_sentiment_distribution.png", dpi=150)
plt.close()

# 6c. Monthly sentiment trend
plt.figure(figsize=(11, 5))
plt.plot(monthly_trend["month"], monthly_trend["avg_sentiment_score"], marker="o", color="#2E86AB", linewidth=2)
plt.axhline(0, color="grey", linestyle="--", linewidth=0.8)
plt.xticks(rotation=45, ha="right")
plt.ylabel("Avg Sentiment Score")
plt.title("Monthly Guest Sentiment Trend (2024)")
plt.tight_layout()
plt.savefig("outputs/03_monthly_sentiment_trend.png", dpi=150)
plt.close()

# 6d. Top negative keywords
plt.figure(figsize=(9, 5))
plt.barh(keyword_df["keyword"][::-1], keyword_df["frequency"][::-1], color="#E63946")
plt.xlabel("Frequency in Negative Reviews")
plt.title("Top Recurring Complaint Keywords")
plt.tight_layout()
plt.savefig("outputs/04_top_negative_keywords.png", dpi=150)
plt.close()

print("\nAll outputs saved to outputs/. Project complete.")

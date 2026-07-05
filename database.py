# database.py
import sqlite3
import os
import re

DB_FILE = "sentiment_analytics.db"


def init_db():
    # Added timeout parameter to handle concurrent write threads smoothly
    with sqlite3.connect(DB_FILE, timeout=20) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS guest_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                review_text TEXT NOT NULL,
                sentiment_verdict TEXT NOT NULL,
                compound_score REAL NOT NULL,
                pos_score REAL NOT NULL,
                neg_score REAL NOT NULL,
                neu_score REAL NOT NULL,
                reply_draft TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS review_aspects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                review_id INTEGER,
                aspect_name TEXT NOT NULL,
                aspect_score REAL,
                aspect_verdict TEXT,
                FOREIGN KEY(review_id) REFERENCES guest_reviews(id) ON DELETE CASCADE
            )
        """)
        conn.commit()


def save_analysis_node(data):
    with sqlite3.connect(DB_FILE, timeout=20) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO guest_reviews (review_text, sentiment_verdict, compound_score, pos_score, neg_score, neu_score, reply_draft)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data['raw_text'], data['sentiment'], data['compound'],
            data['scores']['pos'], data['scores']['neg'], data['scores']['neu'], data['reply_draft']
        ))

        review_id = cursor.lastrowid

        for aspect in data['aspect_map']:
            cursor.execute("""
                INSERT INTO review_aspects (review_id, aspect_name, aspect_score, aspect_verdict) 
                VALUES (?, ?, ?, ?)
            """, (review_id, aspect['name'], aspect['score'], aspect['verdict']))
        conn.commit()


def get_aggregated_metrics():
    with sqlite3.connect(DB_FILE, timeout=20) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT sentiment_verdict, COUNT(*) FROM guest_reviews GROUP BY sentiment_verdict")
        sentiment_rows = cursor.fetchall()
        summary = {"Positive": 0, "Negative": 0, "Neutral": 0}
        for row in sentiment_rows:
            summary[row[0]] = row[1]

        cursor.execute("SELECT aspect_name, COUNT(*) FROM review_aspects GROUP BY aspect_name")
        aspect_rows = cursor.fetchall()
        aspects_summary = {"Staff & Service": 0, "Cleanliness & Room": 0, "Food & Dining": 0, "Value & Price": 0,
                           "General": 0}
        for row in aspect_rows:
            if row[0] in aspects_summary:
                aspects_summary[row[0]] = row[1]

    return summary, aspects_summary


def get_word_frequencies():
    with sqlite3.connect(DB_FILE, timeout=20) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT review_text FROM guest_reviews")
        rows = cursor.fetchall()

    stop_words = {'the', 'and', 'was', 'to', 'is', 'in', 'it', 'of', 'i', 'for', 'with', 'but', 'hotel', 'stay', 'room',
                  'at', 'this', 'we', 'our', 'were', 'had', 'my', 'so', 'that'}
    word_counts = {}
    for row in rows:
        words = re.findall(r'\b[a-zA-Z]{3,}\b', row[0].lower())
        for word in words:
            if word not in stop_words:
                word_counts[word] = word_counts.get(word, 0) + 1
    return sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:12]


def get_chronological_trends():
    with sqlite3.connect(DB_FILE, timeout=20) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT strftime('%Y-%m-%d', timestamp) as date_string,
                   SUM(CASE WHEN sentiment_verdict='Positive' THEN 1 ELSE 0 END),
                   SUM(CASE WHEN sentiment_verdict='Negative' THEN 1 ELSE 0 END),
                   SUM(CASE WHEN sentiment_verdict='Neutral' THEN 1 ELSE 0 END)
            FROM guest_reviews 
            GROUP BY date_string 
            ORDER BY date_string ASC 
            LIMIT 10
        """)
        timeline_rows = cursor.fetchall()
    return timeline_rows
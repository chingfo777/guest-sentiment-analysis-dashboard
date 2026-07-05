# app.py
from flask import Flask, render_template, request, redirect, url_for
from database import init_db, save_analysis_node, get_aggregated_metrics, get_word_frequencies, get_chronological_trends
from analyzer import analyze_guest_review
import pandas as pd
import os
import sqlite3
from database import DB_FILE

app = Flask(__name__)
init_db()

print("Initializing fresh session... Flushing previous operational metrics.")
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()
cursor.execute("DELETE FROM guest_reviews")
cursor.execute("DELETE FROM review_aspects")
conn.commit()
conn.close()

# Ensure temporary upload directory framework exists securely
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/', methods=['GET', 'POST'])
def dashboard():
    last_processed_result = None
    is_single_mode = False

    batch_count = 0
    if request.method == 'GET':
        import sqlite3
        from database import DB_FILE
        print("Page refresh detected. Flushing database metrics for a clean slate.")
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM guest_reviews")
        cursor.execute("DELETE FROM review_aspects")
        conn.commit()
        conn.close()

    if request.method == 'POST':
        # TRACK 1: HANDLE SINGLE TEXT SUBMISSION
        if 'review_text' in request.form and request.form.get('review_text').strip():
            review_text = request.form.get('review_text').strip()
            last_processed_result = analyze_guest_review(review_text)
            save_analysis_node(last_processed_result)
            is_single_mode = True

        # TRACK 2: HANDLE BULK SPREADSHEET BATCH FILE UPLOAD
        elif 'spreadsheet_file' in request.files:
            file = request.files['spreadsheet_file']
            if file and file.filename != '':
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(file_path)
                try:
                    if file.filename.endswith('.csv'):
                        df = pd.read_csv(file_path)
                    else:
                        df = pd.read_excel(file_path)

                    target_col = None
                    possible_headers = ['review', 'text', 'feedback', 'comments', 'review_text']
                    for col in df.columns:
                        if str(col).lower() in possible_headers:
                            target_col = col
                            break
                    if target_col is None:
                        target_col = df.columns[0]

                    for index, row in df.iterrows():
                        raw_review = str(row[target_col]).strip()
                        if raw_review and raw_review != 'nan':
                            analysis = analyze_guest_review(raw_review)
                            save_analysis_node(analysis)
                except Exception as e:
                    print(f"Error: {e}")
                finally:
                    if os.path.exists(file_path):
                        os.remove(file_path)


    # Update inside app.py dashboard route logic section:

    # Fetch unified database telemetry arrays
    sentiment_distribution, aspect_distribution = get_aggregated_metrics()
    word_cloud_matrix = get_word_frequencies()
    timeline_trend_matrix = get_chronological_trends()

    # NEW CORE EXPLICIT DATABASE LOG INJECTION FOR VIEW-BATCH DATATABLE
    import sqlite3
    from database import DB_FILE
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Pull top 50 rows from schema safely ordered chronologically
    cursor.execute(
        "SELECT id, strftime('%Y-%m-%d %H:%M', timestamp), review_text, sentiment_verdict, round(compound_score, 2) FROM guest_reviews ORDER BY id DESC LIMIT 50")
    table_rows_matrix = cursor.fetchall()
    conn.close()

    return render_template(
        'index.html',
        result=last_processed_result,
        s_data=sentiment_distribution,
        a_data=aspect_distribution,
        cloud_words=word_cloud_matrix,
        timeline_data=timeline_trend_matrix,
        table_rows=table_rows_matrix,  # <-- Pass rows array cleanly to template matrix bindings
        is_single_mode = is_single_mode
    )


if __name__ == '__main__':
    app.run(debug=True, port=5001)
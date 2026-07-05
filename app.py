# app.py
from flask import Flask, render_template, request, redirect, url_for
from database import init_db, save_analysis_node, get_aggregated_metrics, get_word_frequencies, get_chronological_trends
from analyzer import analyze_guest_review
import pandas as pd
import os
import sqlite3
from database import DB_FILE
# app.py - Add this endpoint to handle on-the-fly CSV generation
import csv
from io import StringIO
from flask import Response

app = Flask(__name__)
import nltk

try:
    nltk.data.find('sentiment/vader_lexicon.zip')
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    print("Render Inbound Cache: Downloading missing NLTK packages...")
    nltk.download('vader_lexicon', quiet=True)
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)
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


# app.py dashboard handler refactor

@app.route('/', methods=['GET', 'POST'])
def dashboard():
    last_processed_result = None
    is_single_mode = False

    # SAFE REFRESH TRACKING LAYER:
    # Only clear metrics if it's a pure browser navigation line call (no bulk file redirect flags)
    if request.method == 'GET' and not request.args.get('processed'):
        import sqlite3
        from database import DB_FILE
        try:
            with sqlite3.connect(DB_FILE, timeout=20) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM guest_reviews")
                cursor.execute("DELETE FROM review_aspects")
                conn.commit()
                print("Database tables flushed successfully via structural GET refresh tracker.")
        except Exception as e:
            print(f"Non-fatal bypass on refresh lock: {e}")

    if request.method == 'POST':
        # 1. Single text processing track
        if 'review_text' in request.form and request.form.get('review_text').strip():
            review_text = request.form.get('review_text').strip()
            last_processed_result = analyze_guest_review(review_text)
            save_analysis_node(last_processed_result)
            is_single_mode = True

        # 2. Spreadsheet bulk data track
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
                    print(f"Bulk ingestion engine failure logs: {e}")
                finally:
                    if os.path.exists(file_path):
                        os.remove(file_path)

                # FIXED: Redirect with an explicit argument flag to tell the GET controller NOT to clear data
                return redirect(url_for('dashboard', processed=True))

    # Pull out analytical summaries safely
    sentiment_distribution, aspect_distribution = get_aggregated_metrics()
    word_cloud_matrix = get_word_frequencies()
    timeline_trend_matrix = get_chronological_trends()
    import sqlite3
    from database import DB_FILE
    with sqlite3.connect(DB_FILE, timeout=20) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, strftime('%Y-%m-%d %H:%M', timestamp), review_text, sentiment_verdict, round(compound_score, 2) FROM guest_reviews ORDER BY id DESC LIMIT 50")
        table_rows_matrix = cursor.fetchall()

    return render_template(
        'index.html',
        result=last_processed_result,
        s_data=sentiment_distribution,
        a_data=aspect_distribution,
        cloud_words=word_cloud_matrix,
        timeline_data=timeline_trend_matrix,
        table_rows=table_rows_matrix,
        is_single_mode=is_single_mode
    )





@app.route('/export-dataset')
def export_dataset():
    """Queries the live relational tables and streams a clean CSV file attachment."""
    import sqlite3
    import csv
    from io import StringIO
    from flask import Response
    from database import DB_FILE

    # 1. Open string stream memory buffer
    si = StringIO()
    cw = csv.writer(si)

    # 2. Write CSV Header Matrix
    cw.writerow(['Record ID', 'Timestamp', 'Raw Review Text', 'Global Sentiment', 'Compound Score', 'Target Aspect',
                 'Aspect Valence Score', 'Aspect Verdict'])

    # 3. Pull data rows using an INNER JOIN across our relational tables
    try:
        with sqlite3.connect(DB_FILE, timeout=20) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT r.id, r.timestamp, r.review_text, r.sentiment_verdict, r.compound_score,
                       a.aspect_name, a.aspect_score, a.aspect_verdict
                FROM guest_reviews r
                LEFT JOIN review_aspects a ON r.id = a.review_id
                ORDER BY r.id DESC
            """)
            rows = cursor.fetchall()

            for row in rows:
                cw.writerow(row)
    except Exception as e:
        print(f"Export engine runtime exception: {e}")
        # cw.writerow(["Error generating export telemetry logs", str(e)])

    # 4. Create response object pointing to attachment configuration structures
    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=sentix_executive_report.csv"}
    )


# app.py - Explicit Database Truncation Route Handler
@app.route('/clear-all', methods=['POST'])
def clear_all_data():
    """Wipes out all tables in the SQLite database to reset the application state."""
    import sqlite3
    from database import DB_FILE
    try:
        with sqlite3.connect(DB_FILE, timeout=20) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM guest_reviews")
            cursor.execute("DELETE FROM review_aspects")
            conn.commit()
            print("Database completely flushed via explicit Clear All action button request.")
    except Exception as e:
        print(f"Exception encountered during manual data wipe: {e}")

    # Redirect cleanly to show the empty dormant state placeholder
    return redirect(url_for('dashboard'))
if __name__ == '__main__':
    import os
    init_db()
    # Render dynamic port allocation matrix
    port = int(os.environ.get("PORT", 5001))
    app.run(host='0.0.0.0', port=port)
# app.py
from flask import Flask, render_template, request, redirect, url_for
from database import init_db, save_analysis_node, get_aggregated_metrics, get_word_frequencies, get_chronological_trends
from analyzer import analyze_guest_review
import pandas as pd
import os

app = Flask(__name__)
init_db()

# Ensure temporary upload directory framework exists securely
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/', methods=['GET', 'POST'])
def dashboard():
    last_processed_result = None
    batch_count = 0

    if request.method == 'POST':
        # TRACK 1: HANDLE SINGLE TEXT SUBMISSION
        if 'review_text' in request.form and request.form.get('review_text').strip():
            review_text = request.form.get('review_text').strip()
            last_processed_result = analyze_guest_review(review_text)
            save_analysis_node(last_processed_result)

        # TRACK 2: HANDLE BULK SPREADSHEET BATCH FILE UPLOAD
        elif 'spreadsheet_file' in request.files:
            file = request.files['spreadsheet_file']
            if file and file.filename != '':
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(file_path)

                # Load sheet array using Pandas safely based on extension token
                try:
                    if file.filename.endswith('.csv'):
                        df = pd.read_csv(file_path)
                    else:
                        df = pd.read_excel(file_path)

                    # Locate the column containing textual data dynamically
                    # It searches for common headers like 'review', 'text', 'feedback', or falls back to column 0
                    target_col = None
                    possible_headers = ['review', 'text', 'feedback', 'comments', 'review_text']
                    for col in df.columns:
                        if str(col).lower() in possible_headers:
                            target_col = col
                            break
                    if target_col is None:
                        target_col = df.columns[0]

                    # Core batch compilation matrix loop execution
                    for index, row in df.iterrows():
                        raw_review = str(row[target_col]).strip()
                        if raw_review and raw_review != 'nan':
                            # Execute the NLP pipelines over each entity row
                            analysis = analyze_guest_review(raw_review)
                            save_analysis_node(analysis)
                            batch_count += 1

                except Exception as e:
                    print(f"Spreadsheet compilation pipeline exception track: {e}")
                finally:
                    # Clean up the file out of storage after execution completes
                    if os.path.exists(file_path):
                        os.remove(file_path)

                # Redirect natively to refresh state data and plot charts perfectly
                return redirect(url_for('dashboard'))

    # Fetch unified aggregates database tracking structures
    sentiment_distribution, aspect_distribution = get_aggregated_metrics()
    word_cloud_matrix = get_word_frequencies()
    timeline_trend_matrix = get_chronological_trends()

    return render_template(
        'index.html',
        result=last_processed_result,
        s_data=sentiment_distribution,
        a_data=aspect_distribution,
        cloud_words=word_cloud_matrix,
        timeline_data=timeline_trend_matrix
    )


if __name__ == '__main__':
    app.run(debug=True, port=5001)
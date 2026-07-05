# analyzer.py
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from textblob import TextBlob
import re

# Safely verify and download the required VADER lexicon dependency on initialization
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon', quiet=True)

# Initialize the Lexicon-Based Intensity Analyzer globally
sia = SentimentIntensityAnalyzer()


def analyze_guest_review(review_text):
    """
    Advanced Hybrid NLP Pipeline.
    Combines NLTK VADER Lexicon scoring with TextBlob structural subjectivity
    analysis, maps aspect-based rule metrics, and builds response payloads.
    """
    # 1. Compute VADER Polarities
    vader_scores = sia.polarity_scores(review_text)
    compound = vader_scores['compound']

    # 2. Compute TextBlob Subjectivity Layer (0.0 = Objective, 1.0 = Highly Subjective)
    blob = TextBlob(review_text)
    subjectivity_percentage = round(blob.sentiment.subjectivity * 100, 1)

    # 3. Categorize Final Sentiment Verdict based on Standard Academic Intervals
    if compound >= 0.05:
        sentiment = "Positive"
    elif compound <= -0.05:
        sentiment = "Negative"
    else:
        sentiment = "Neutral"

    # 4. Aspect-Based Feature Extraction Mapping (Heuristic Sub-classification)
    categories = {
        "Staff & Service": ["staff", "service", "manager", "waiter", "reception", "rude", "helpful", "friendly",
                            "hospitality", "clerk", "crew"],
        "Cleanliness & Room": ["room", "bed", "bathroom", "dirty", "clean", "shower", "towel", "pillow", "smell", "ac",
                               "wifi", "sheets"],
        "Food & Dining": ["food", "breakfast", "dinner", "restaurant", "delicious", "tasty", "buffet", "coffee", "menu",
                          "meals", "bar"],
        "Value & Price": ["price", "expensive", "cheap", "worth", "money", "cost", "overpriced", "billing", "rates",
                          "charge", "affordable"]
    }

    detected_aspects = []
    lowered_text = review_text.lower()

    for aspect, keywords in categories.items():
        # Match keywords using strict word boundaries to avoid false substring matches
        if any(re.search(rf'\b{kw}\b', lowered_text) for kw in keywords):
            detected_aspects.append(aspect)

    # Default fallback element if no strict categories are triggered
    if not detected_aspects:
        detected_aspects.append("General")

    # 5. Generative Contextual CRM Response Draft Generator
    aspect_string = ", ".join(detected_aspects)
    if sentiment == "Negative":
        reply_draft = f"Dear Guest, thank you for sharing your feedback with us. We deeply regret that your experience regarding {aspect_string} did not align with our quality standards. Our operational teams have been notified to review these parameters immediately."
    elif sentiment == "Positive":
        reply_draft = f"Thank you so much for your exceptional rating! We are delighted to hear our focus on {aspect_string} made your stay memorable. We look forward to welcoming you back during your next visit."
    else:
        reply_draft = f"Dear Guest, thank you for taking the time to share your review. We appreciate your objective assessment regarding {aspect_string} and will use it to continually refine our guest journey benchmarks."

    # Return unified data payload structured perfectly for SQLite insertion rules
    return {
        "raw_text": review_text,
        "sentiment": sentiment,
        "compound": compound,
        "confidence": round(abs(compound) * 100, 1),
        "subjectivity": subjectivity_percentage,
        "aspects": detected_aspects,
        "reply_draft": reply_draft,
        "scores": {
            "pos": round(vader_scores['pos'] * 100, 1),
            "neg": round(vader_scores['neg'] * 100, 1),
            "neu": round(vader_scores['neu'] * 100, 1)
        }
    }


# =====================================================================
# SYSTEM VERIFICATION BLOCK
# Allows isolated component debugging directly inside the terminal window
# =====================================================================
if __name__ == "__main__":
    sample_text = "The room was incredibly dirty and the reception staff was quite rude, but the breakfast food was delicious."
    print("Executing standalone pipeline diagnostics testing matrix...\n")
    diagnostics_result = analyze_guest_review(sample_text)

    import json

    print(json.dumps(diagnostics_result, indent=4))
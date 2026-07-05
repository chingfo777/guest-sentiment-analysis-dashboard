# analyzer.py
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from textblob import TextBlob
import re

try:
    nltk.data.find('sentiment/vader_lexicon.zip')
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('vader_lexicon', quiet=True)
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)

sia = SentimentIntensityAnalyzer()


def analyze_guest_review(review_text):
    """
    Advanced Multi-Aspect Fine-Grained Sentiment Parser.
    Tokenizes text into independent clauses to score individual operational aspects.
    """
    # Global metrics
    global_vader = sia.polarity_scores(review_text)
    global_compound = global_vader['compound']

    blob = TextBlob(review_text)
    subjectivity_percentage = round(blob.sentiment.subjectivity * 100, 1)

    if global_compound >= 0.05:
        global_sentiment = "Positive"
    elif global_compound <= -0.05:
        global_sentiment = "Negative"
    else:
        global_sentiment = "Neutral"

    # Aspect configuration map
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

    # Sentence Tokenization for Fine-Grained Analysis
    sentences = nltk.sent_tokenize(review_text)
    aspect_scores = {}
    detected_aspects = []

    for sentence in sentences:
        lowered_sentence = sentence.lower()
        sentence_vader = sia.polarity_scores(sentence)
        sentence_compound = sentence_vader['compound']

        for aspect, keywords in categories.items():
            if any(re.search(rf'\b{kw}\b', lowered_sentence) for kw in keywords):
                if aspect not in aspect_scores:
                    aspect_scores[aspect] = []
                aspect_scores[aspect].append(sentence_compound)
                if aspect not in detected_aspects:
                    detected_aspects.append(aspect)

    if not detected_aspects:
        detected_aspects.append("General")
        aspect_scores["General"] = [global_compound]

    # Calculate final fine-grained average valence per aspect
    final_aspect_map = []
    for aspect, scores in aspect_scores.items():
        avg_score = sum(scores) / len(scores)
        if avg_score >= 0.05:
            verdict = "Positive"
        elif avg_score <= -0.05:
            verdict = "Negative"
        else:
            verdict = "Neutral"
        final_aspect_map.append({
            "name": aspect,
            "score": round(avg_score, 2),
            "verdict": verdict
        })

    # Contextual CRM Response Draft Framework builder
    aspect_strings = [f"{a['name']} ({a['verdict']})" for a in final_aspect_map]
    reply_draft = f"Dear Guest, thank you for your feedback. We have evaluated your individual metric markers: {', '.join(aspect_strings)}. Your assessments have been forwarded directly to their respective department supervisors to align with our corporate standards."

    return {
        "raw_text": review_text,
        "sentiment": global_sentiment,
        "compound": global_compound,
        "confidence": round(abs(global_compound) * 100, 1),
        "subjectivity": subjectivity_percentage,
        "aspects": detected_aspects,
        "aspect_map": final_aspect_map,  # Structured multi-verdict engine mapping array
        "reply_draft": reply_draft,
        "scores": {
            "pos": round(global_vader['pos'] * 100, 1),
            "neg": round(global_vader['neg'] * 100, 1),
            "neu": round(global_vader['neu'] * 100, 1)
        }
    }
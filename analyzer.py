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


def detect_sarcasm(text):
    """
    Linguistic Rule Matrix for Sarcasm Detection.
    Tracks sentiment contrast shifts and emotional flips within the text sequence.
    """
    lowered = text.lower()

    # 1. Define explicit linguistic anchors
    positive_anchors = ["thanks", "thank you", "great", "amazing", "wonderful", "excellent", "loved the", "brilliant"]
    negative_anchors = ["worst", "terrible", "horrible", "disaster", "trash", "waste", "broken", "rude", "nightmare"]

    # 2. Check for Contrast Shift (e.g., Positive anchor followed by a Negative anchor)
    has_positive = any(re.search(rf'\b{word}\b', lowered) for word in positive_anchors)
    has_negative = any(re.search(rf'\b{word}\b', lowered) for word in negative_anchors)

    is_sarcastic = False

    if has_positive and has_negative:
        # Check if the positive anchor appears before the negative friction point
        for pos_w in positive_anchors:
            for neg_w in negative_anchors:
                pos_idx = lowered.find(pos_w)
                neg_idx = lowered.find(neg_w)
                if 0 <= pos_idx < neg_idx:
                    is_sarcastic = True
                    break

    # 3. Check for Exaggerated Mockery (e.g., "Wow, what a 'clean' room!!!")
    if "!!!" in text or "?!?" in text:
        if any(w in lowered for w in ["wow", "oh boy", "love it when"]):
            is_sarcastic = True

    return is_sarcastic


def analyze_guest_review(review_text):
    """
    Advanced Multi-Aspect Fine-Grained Sentiment Parser with Sarcasm Mitigation Matrix.
    """
    global_vader = sia.polarity_scores(review_text)
    global_compound = global_vader['compound']

    # Trigger the rule matrix
    sarcasm_detected = detect_sarcasm(review_text)

    # ACADEMIC OVERRIDE RULES: If sarcasm is captured, manually penalize the compound valence
    if sarcasm_detected:
        global_compound = min(global_compound, -0.6)  # Force a high-confidence negative score

    blob = TextBlob(review_text)
    subjectivity_percentage = round(blob.sentiment.subjectivity * 100, 1)

    if global_compound >= 0.05:
        global_sentiment = "Positive"
    elif global_compound <= -0.05:
        global_sentiment = "Negative"
    else:
        global_sentiment = "Neutral"

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

    sentences = nltk.sent_tokenize(review_text)
    aspect_scores = {}
    detected_aspects = []

    for sentence in sentences:
        lowered_sentence = sentence.lower()
        sentence_vader = sia.polarity_scores(sentence)
        sentence_compound = sentence_vader['compound']

        # Apply local sentence sarcasm weight if triggered
        if detect_sarcasm(sentence):
            sentence_compound = -0.7

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

    aspect_strings = [f"{a['name']} ({a['verdict']})" for a in final_aspect_map]

    # Adjust CRM response script if sarcasm matrix flags true
    if sarcasm_detected:
        reply_draft = f"Dear Guest, thank you for your feedback. Our NLP engine flagged high structural irony markers within this submission. We recognize the severe issues regarding your operational layers ({', '.join(aspect_strings)}) and are accelerating this ticket directly to the General Manager for immediate response."
    else:
        reply_draft = f"Dear Guest, thank you for your feedback. We have evaluated your individual metric markers: {', '.join(aspect_strings)}. Your assessments have been forwarded directly to their respective department supervisors."

    return {
        "raw_text": review_text,
        "sentiment": global_sentiment,
        "compound": global_compound,
        "confidence": round(abs(global_compound) * 100, 1),
        "subjectivity": subjectivity_percentage,
        "aspects": detected_aspects,
        "aspect_map": final_aspect_map,
        "reply_draft": reply_draft,
        "sarcasm_flag": "Yes" if sarcasm_detected else "No",  # <-- Dynamic telemetry flag
        "scores": {
            "pos": round(global_vader['pos'] * 100, 1),
            "neg": round(global_vader['neg'] * 100, 1),
            "neu": round(global_vader['neu'] * 100, 1)
        }
    }
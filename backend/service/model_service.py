from pathlib import Path
import joblib
from .escalation_service import get_escalation


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"


# ============================================================
# LOAD MODEL
# ============================================================

def load_model(file_name: str):
    return joblib.load(MODELS_DIR / file_name)


# ============================================================
# LOAD MODELS
# ============================================================

sentiment_model = load_model("sentiment_model.pkl")
emotion_model = load_model("emotion_model.pkl")
intent_model = load_model("intent_model.pkl")
topic_model = load_model("topic_model.pkl")
urgency_model = load_model("urgency_model.pkl")


# Separate TF-IDF pipeline used by topic model
tfidf_pipeline = load_model("tfidf_pipeline.pkl")


# ============================================================
# CALCULATE PREDICTION
# ============================================================

def calculate_prediction(probabilities, classes):
    """
    Calculate:
    - predicted label
    - confidence score
    - margin between top two predictions
    """

    # Sort probability indices from highest to lowest
    sorted_indices = probabilities.argsort()[::-1]

    # Highest probability prediction
    best_index = sorted_indices[0]

    # Second highest probability prediction
    second_index = sorted_indices[1]

    best_probability = float(probabilities[best_index])
    second_probability = float(probabilities[second_index])

    # Difference between first and second prediction
    margin = best_probability - second_probability

    return {
        "label": str(classes[best_index]),
        "score": round(best_probability, 4),
        "margin": round(margin, 4)
    }


# ============================================================
# NORMAL MODEL PREDICTION
# ============================================================

def predict(model, text):
    """
    Used for:
    - sentiment
    - emotion
    - intent
    - urgency

    These models are complete sklearn pipelines,
    so they accept raw text directly.
    """

    probabilities = model.predict_proba([text])[0]
    classes = model.classes_

    return calculate_prediction(probabilities, classes)


# ============================================================
# TOPIC PREDICTION
# ============================================================

def predict_topic(text):
    """
    Topic model is different from the other models.

    It is a classifier-only model, so we must first
    transform the text using the separate TF-IDF pipeline.
    """

    # Convert text into numerical TF-IDF features
    X = tfidf_pipeline.transform([text])

    # Get topic probabilities
    probabilities = topic_model.predict_proba(X)[0]

    # Get topic labels
    classes = topic_model.classes_

    return calculate_prediction(probabilities, classes)


# ============================================================
# CLASSIFICATION
# ============================================================

print("Model service loaded successfully")


def classify_text(text: str):

    print("before classification")

    # --------------------------------------------------------
    # SENTIMENT
    # --------------------------------------------------------

    sentiment = predict(sentiment_model, text)

    print("sentiment model")


    # --------------------------------------------------------
    # EMOTION
    # --------------------------------------------------------

    emotion = predict(emotion_model, text)

    print("emotion model")


    # --------------------------------------------------------
    # INTENT
    # --------------------------------------------------------

    intent = predict(intent_model, text)

    print("intent model")


    # --------------------------------------------------------
    # TOPIC
    # --------------------------------------------------------

    topic = predict_topic(text)

    print("topic model")


    # --------------------------------------------------------
    # URGENCY
    # --------------------------------------------------------

    urgency = predict(urgency_model, text)

    print("urgency model")


    # ========================================================
    # FINAL PREDICTION FORMAT
    # ========================================================

    # IMPORTANT:
    # We are keeping the same prediction structure that
    # your existing escalation_service expects.
    #
    # The new "margin" values are NOT sent here yet.
    # They are available in the individual prediction
    # dictionaries for our upcoming hybrid classifier.

    prediction = [
        {
            "sentiment": sentiment["label"],
            "score": sentiment["score"]
        },
        {
            "emotion": emotion["label"],
            "score": emotion["score"]
        },
        {
            "intent": intent["label"],
            "score": intent["score"]
        },
        {
            "topic": topic["label"],
            "score": topic["score"]
        },
        {
            "urgency": urgency["label"],
            "score": urgency["score"]
        }
    ]


    # ========================================================
    # ESCALATION
    # ========================================================

    escalation = get_escalation(prediction)


    # ========================================================
    # RETURN RESULT
    # ========================================================

    return {
        "prediction": prediction,
        "escalation": escalation
    }
from pathlib import Path
import joblib
from .escalation_service import get_escalation

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"


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
# PREDICTION
# ============================================================

def predict(model, text):

    probabilities = model.predict_proba([text])[0]
    classes = model.classes_

    index = probabilities.argmax()

    return {
        "label": str(classes[index]),
        "score": round(float(probabilities[index]), 4)
    }


def predict_topic(text):

    # Convert text into the numerical features expected
    # by the standalone topic classifier
    X = tfidf_pipeline.transform([text])

    probabilities = topic_model.predict_proba(X)[0]
    classes = topic_model.classes_

    index = probabilities.argmax()

    return {
        "label": str(classes[index]),
        "score": round(float(probabilities[index]), 4)
    }


# ============================================================
# CLASSIFICATION
# ============================================================

print("Model service loaded successfully")


def classify_text(text: str):

    print("before classification")

    # These four models are complete pipelines.
    # They accept raw text directly.
    sentiment = predict(sentiment_model, text)
    print("sentiment model")

    emotion = predict(emotion_model, text)
    print("emotion model")

    intent = predict(intent_model, text)
    print("intent model")

    # Topic model is classifier-only, so it needs
    # the separate TF-IDF transformation.
    topic = predict_topic(text)
    print("topic model")

    urgency = predict(urgency_model, text)
    print("urgency model")

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

    escalation = get_escalation(prediction)

    return {
        "prediction": prediction,
        "escalation": escalation
    }
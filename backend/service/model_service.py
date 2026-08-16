from pathlib import Path
import joblib
from .escalation_service import get_escalation

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"


def load_model(file_name: str):
    return joblib.load(MODELS_DIR / file_name)


sentiment_model = load_model("sentiment_model.pkl")
emotion_model = load_model("emotion_model.pkl")
intent_model = load_model("intent_model.pkl")
topic_model = load_model("topic_model.pkl")
urgency_model = load_model("urgency_model.pkl")


def predict(model, text):

    probabilities = model.predict_proba([text])[0]
    classes = model.classes_

    index = probabilities.argmax()

    return {
        "label": str(classes[index]),
        "score": round(float(probabilities[index]), 4)
    }


def classify_text(text: str):

    sentiment = predict(sentiment_model, text)
    emotion = predict(emotion_model, text)
    intent = predict(intent_model, text)
    topic = predict(topic_model, text)
    urgency = predict(urgency_model, text)

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
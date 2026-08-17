from .model_service import (
    sentiment_model,
    emotion_model,
    intent_model,
    urgency_model,
    predict,
    predict_topic
)

from .llm_service import classify_with_llm
from .escalation_service import get_escalation


# ============================================================
# ML CLASSIFICATION
# ============================================================

def classify_with_ml(text: str):

    sentiment = predict(sentiment_model, text)
    emotion = predict(emotion_model, text)
    intent = predict(intent_model, text)
    topic = predict_topic(text)
    urgency = predict(urgency_model, text)

    return {
        "sentiment": sentiment["label"],
        "emotion": emotion["label"],
        "intent": intent["label"],
        "topic": topic["label"],
        "urgency": urgency["label"]
    }


# ============================================================
# ML CONFIDENCE CHECK
# ============================================================

def get_ml_confidence(text: str):

    sentiment = predict(sentiment_model, text)
    emotion = predict(emotion_model, text)
    intent = predict(intent_model, text)
    topic = predict_topic(text)
    urgency = predict(urgency_model, text)

    predictions = {
        "sentiment": sentiment,
        "emotion": emotion,
        "intent": intent,
        "topic": topic,
        "urgency": urgency
    }

    return predictions


# ============================================================
# CONVERT LABEL DICTIONARY TO APPLICATION FORMAT
# ============================================================

def build_prediction(labels: dict):

    return [
        {
            "sentiment": labels["sentiment"],
            "score": 0.0
        },
        {
            "emotion": labels["emotion"],
            "score": 0.0
        },
        {
            "intent": labels["intent"],
            "score": 0.0
        },
        {
            "topic": labels["topic"],
            "score": 0.0
        },
        {
            "urgency": labels["urgency"],
            "score": 0.0
        }
    ]


# ============================================================
# HYBRID CLASSIFICATION
# ============================================================

def hybrid_classify(text: str):

    print("\n" + "=" * 70)
    print("HYBRID CLASSIFICATION")
    print("=" * 70)

    # --------------------------------------------------------
    # STEP 1: ML prediction
    # --------------------------------------------------------

    ml_results = get_ml_confidence(text)

    print("\nML PREDICTION:")
    print("-" * 70)

    for name, result in ml_results.items():

        print(
            f"{name:<10} "
            f"label={result['label']:<20} "
            f"score={result['score']:.4f} "
            f"margin={result['margin']:.4f}"
        )

    # --------------------------------------------------------
    # STEP 2: Check ML confidence
    # --------------------------------------------------------

    CONFIDENCE_THRESHOLD = 0.90
    MARGIN_THRESHOLD = 0.20

    uncertain = False

    for name, result in ml_results.items():

        if result["score"] < CONFIDENCE_THRESHOLD:
            print(f"→ {name} has low confidence")
            uncertain = True

        elif result["margin"] < MARGIN_THRESHOLD:
            print(f"→ {name} has low prediction margin")
            uncertain = True

    # --------------------------------------------------------
    # STEP 3: Convert ML results to simple labels
    # --------------------------------------------------------

    ml_prediction = {
        "sentiment": ml_results["sentiment"]["label"],
        "emotion": ml_results["emotion"]["label"],
        "intent": ml_results["intent"]["label"],
        "topic": ml_results["topic"]["label"],
        "urgency": ml_results["urgency"]["label"]
    }

    # --------------------------------------------------------
    # STEP 4: ML is confident
    # --------------------------------------------------------

    if not uncertain:

        print("\nML prediction is confident.")
        print("Gemini checker not required.")

        final_labels = ml_prediction

    # --------------------------------------------------------
    # STEP 5: ML is uncertain → Gemini checks
    # --------------------------------------------------------

    else:

        print("\nML prediction is uncertain.")
        print("Sending prediction to Gemini for verification...")

        try:

            final_labels = classify_with_llm(
                text,
                ml_prediction
            )

            print("\nGemini checker completed.")

        except Exception as error:

            print("\nGemini unavailable.")
            print(type(error).__name__)
            print(str(error))

            print("Falling back to ML prediction.")

            final_labels = ml_prediction

    # --------------------------------------------------------
    # STEP 6: Build application prediction
    # --------------------------------------------------------

    prediction = build_prediction(final_labels)

    # --------------------------------------------------------
    # STEP 7: Escalation
    # --------------------------------------------------------

    escalation = get_escalation(prediction)

    # --------------------------------------------------------
    # STEP 8: Final result
    # --------------------------------------------------------

    return {
        "prediction": prediction,
        "escalation": escalation
    }
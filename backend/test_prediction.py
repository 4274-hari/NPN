from service.model_service import (
    sentiment_model,
    emotion_model,
    intent_model,
    urgency_model,
    predict,
    predict_topic
)


text = "what the hell is the service provided?"

print("\nTEXT:")
print(text)

print("\nML PREDICTIONS")
print("=" * 75)

sentiment = predict(sentiment_model, text)
emotion = predict(emotion_model, text)
intent = predict(intent_model, text)
topic = predict_topic(text)
urgency = predict(urgency_model, text)


results = {
    "sentiment": sentiment,
    "emotion": emotion,
    "intent": intent,
    "topic": topic,
    "urgency": urgency
}


for name, result in results.items():

    print(
        f"{name:10} "
        f"label={result['label']:20} "
        f"score={result['score']:.4f} "
        f"margin={result['margin']:.4f}"
    )
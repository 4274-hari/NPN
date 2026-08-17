from service.rag_service import generate_reply


text = "the wifi service was good"

labels = {
    "sentiment": "positive",
    "emotion": "joy",
    "intent": "praise",
    "topic": "service",
    "urgency": "low"
}

print("=" * 70)
print("RAG + GROQ REPLY TEST")
print("=" * 70)

try:

    reply = generate_reply(
        text,
        labels,
        ""
    )

    print("\nGENERATED REPLY:")
    print("-" * 70)
    print(reply)
    print("-" * 70)

except Exception as e:

    print("\nERROR:")
    print(type(e).__name__)
    print(str(e))

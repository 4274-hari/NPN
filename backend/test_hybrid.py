from service.hybrid_classifier import hybrid_classify


print("=" * 70)
print("HYBRID CLASSIFIER - MANUAL TEST")
print("=" * 70)
print("Type a message to classify.")
print("Type 'exit' to stop.")
print()


while True:

    text = input("Enter message: ").strip()

    if text.lower() == "exit":
        print("Testing stopped.")
        break

    if not text:
        print("Please enter a message.")
        continue

    result = hybrid_classify(text)

    print("\nFINAL JSON:")
    print(result)

    print("\n" + "=" * 70 + "\n")
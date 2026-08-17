from service.llm_service import classify_with_llm


text = "what the hell is the service provided?"

result = classify_with_llm(text)

print("\nLLM RESULT:")
print(result)
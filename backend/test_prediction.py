from service.model_service import classify_text

text = "@nexora i am having problems in upgrading"

result = classify_text(text)

print("\nRESULT:")
print(result)
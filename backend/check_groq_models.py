from groq import Groq
from config import settings

client = Groq(api_key=settings.groq_api_key)

print("\nAvailable Groq models:")
print("=" * 60)

models = client.models.list()

for model in models.data:
    print(model.id)
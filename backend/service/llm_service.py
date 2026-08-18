import os
import json
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel


# ============================================================
# ENVIRONMENT
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError(
        f"GEMINI_API_KEY is not set. Checked: {ENV_FILE}"
    )


# ============================================================
# GEMINI CLIENT
# ============================================================

client = genai.Client(api_key=API_KEY)

MODEL_NAME = "gemini-3.5-flash-lite"


# ============================================================
# STRUCTURED OUTPUT MODEL
# ============================================================

class ClassificationResult(BaseModel):

    sentiment: Literal[
        "positive",
        "neutral",
        "negative"
    ]

    emotion: Literal[
        "anger",
        "frustration",
        "joy",
        "neutral",
        "sadness"
    ]

    intent: Literal[
        "complaint",
        "other",
        "praise",
        "query"
    ]

    topic: Literal[
        "account",
        "billing_payment",
        "customer_support",
        "delivery",
        "other",
        "product",
        "refund_cancellation",
        "security",
        "service",
        "subscription_plan",
        "technical"
    ]

    urgency: Literal[
        "high",
        "medium",
        "low"
    ]


# ============================================================
# GEMINI CLASSIFICATION
# ============================================================

def classify_with_llm(text: str, ml_prediction: dict):

    prompt = f"""
You are the final semantic checker for a customer-support
social-media classification system.

Analyze the original user message carefully.

An ML classifier has already produced an initial prediction.
Use it as supporting information, but DO NOT blindly trust it.

Correct the ML prediction if the actual meaning, tone,
context, or wording indicates another classification.

IMPORTANT RULES:

1. Understand the complete message.
2. Consider informal language and slang.
3. Consider emotional wording.
4. Strong words do not automatically mean high urgency.
5. Distinguish questions from complaints.
6. Determine the topic from the actual meaning.
7. Prefer semantic meaning over the ML prediction.

URGENCY:

high:
Immediate or critical problems such as payment loss,
security issues, account access failures, serious service
failures, or problems requiring immediate attention.

medium:
A significant problem or repeated failure that needs support
but is not immediately critical.

low:
General questions, praise, feedback, informational requests,
or minor/non-blocking issues.


ORIGINAL USER MESSAGE:
{text}


INITIAL ML PREDICTION:
{ml_prediction}


Return ONLY a JSON object with exactly these fields:

{{
    "sentiment": "positive|neutral|negative",
    "emotion": "anger|frustration|joy|neutral|sadness",
    "intent": "complaint|other|praise|query",
    "topic": "account|billing_payment|customer_support|delivery|other|product|refund_cancellation|security|service|subscription_plan|technical",
    "urgency": "high|medium|low"
}}
"""

    # ========================================================
    # GEMINI REQUEST
    # ========================================================

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config={
            "temperature": 0,
            "response_mime_type": "application/json",
            "response_schema": ClassificationResult
        }
    )

    # ========================================================
    # DEBUG RESPONSE
    # ========================================================

    print("\nRAW GEMINI RESPONSE:")
    print(response.text)

    # ========================================================
    # PARSE RESPONSE TEXT
    # ========================================================

    if not response.text:
        raise ValueError("Gemini returned an empty response.")

    try:
        data = json.loads(response.text)

    except json.JSONDecodeError as e:
        raise ValueError(
            f"Gemini returned invalid JSON: {e}\n"
            f"Raw response: {response.text}"
        )

    # ========================================================
    # VALIDATE WITH PYDANTIC
    # ========================================================

    result = ClassificationResult.model_validate(data)

    # ========================================================
    # RETURN ONLY THE REQUIRED FIVE FIELDS
    # ========================================================

    return result.model_dump()
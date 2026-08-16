def get_escalation(prediction):
    """
    prediction = output from the classifier
    """

    # Convert list format into easy-to-use dictionary
    result = {}

    for item in prediction:
        key = next(k for k in item if k != "score")
        result[key] = {
            "label": item[key],
            "score": item["score"]
        }

    sentiment = result["sentiment"]
    emotion = result["emotion"]
    intent = result["intent"]
    topic = result["topic"]
    urgency = result["urgency"]

    # --------------------------------
    # 1. RULE-BASED ESCALATION
    # --------------------------------

    if urgency["label"] == "high":
        return {
            "escalation": True,
            "priority": "P1",
            "score": 100,
            "reason": "High urgency"
        }

    if (
        intent["label"] == "complaint"
        and sentiment["label"] == "negative"
        and urgency["label"] in ["medium", "high"]
    ):
        return {
            "escalation": True,
            "priority": "P2",
            "score": 65,
            "reason": "Negative complaint with medium/high urgency"
        }

    # --------------------------------
    # 2. WEIGHTED ESCALATION SCORE
    # --------------------------------

    score = 0

    if sentiment["label"] == "negative":
        score += 20

    if intent["label"] == "complaint":
        score += 25

    if urgency["label"] == "high":
        score += 40
    elif urgency["label"] == "medium":
        score += 20

    if emotion["label"] in ["angry", "frustrated"]:
        score += 20

    # --------------------------------
    # 3. CONFIDENCE
    # --------------------------------

    confidence = (
        sentiment["score"]
        + emotion["score"]
        + intent["score"]
        + topic["score"]
        + urgency["score"]
    ) / 5

    # --------------------------------
    # FINAL DECISION
    # --------------------------------

    if score >= 60 and confidence >= 0.80:
        return {
            "escalation": True,
            "priority": "P2",
            "score": score,
            "confidence": round(confidence, 4),
            "reason": "High escalation score with high confidence"
        }

    elif score >= 40:
        return {
            "escalation": "review",
            "priority": "P3",
            "score": score,
            "confidence": round(confidence, 4),
            "reason": "Requires human review"
        }

    return {
        "escalation": False,
        "priority": "P3",
        "score": score,
        "confidence": round(confidence, 4),
        "reason": "Normal issue"
    }
TOPIC_TEAMS = {
    "technical": "Service & Technical Support",
    "service": "Service & Technical Support",
    "billing_payment": "Billing & Subscription",
    "refund_cancellation": "Billing & Subscription",
    "subscription_plan": "Billing & Subscription",
    "product": "Product & Fulfillment",
    "delivery": "Product & Fulfillment",
    "account": "Account & Security",
    "security": "Account & Security",
    "customer_support": "Customer Support & General",
    "other": "Customer Support & General",
}


def route_topic_to_team(topic: str) -> str:
    return TOPIC_TEAMS.get(topic.strip().lower(), "Customer Support & General")

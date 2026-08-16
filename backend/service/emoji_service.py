import re
import emoji


def process_emojis(text: str) -> str:
    """
    Convert emojis into readable text.
    
    Example:
        "I am happy 😊"
        -> "I am happy smiling face with smiling eyes"
    """

    return emoji.demojize(
        text,
        delimiters=(" ", " ")
    )


def clean_text(text: str) -> str:
    """
    Clean social-media text while preserving
    emoji meaning for the classifier.
    """

    # 1. Convert emoji → words
    text = process_emojis(text)

    # 2. Lowercase
    text = text.lower()

    # 3. Remove URLs
    text = re.sub(
        r"https?://\S+|www\.\S+",
        " ",
        text
    )

    # 4. Remove mentions
    text = re.sub(
        r"@\w+",
        " ",
        text
    )

    # 5. Convert hashtags to normal words
    text = re.sub(
        r"#(\w+)",
        r"\1",
        text
    )

    # 6. Replace underscores from emoji names
    text = text.replace("_", " ")

    # 7. Keep only letters, numbers and spaces
    text = re.sub(
        r"[^a-zA-Z0-9\s]",
        " ",
        text
    )

    # 8. Remove extra spaces
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()
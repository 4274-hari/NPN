import re
import emoji


def process_emojis(text):

    return emoji.demojize(
        text,
        delimiters=(" ", " ")
    )


def clean_text(text):

    # Emoji → words
    text = process_emojis(text)

    # Lowercase
    text = text.lower()

    # Remove URLs
    text = re.sub(
        r"https?://\S+|www\.\S+",
        " ",
        text
    )

    # Remove mentions
    text = re.sub(
        r"@\w+",
        " ",
        text
    )

    # Convert hashtag to normal word
    text = re.sub(
        r"#(\w+)",
        r"\1",
        text
    )

    # Keep letters, numbers, underscore and spaces
    text = re.sub(
        r"[^a-zA-Z0-9_\s]",
        " ",
        text
    )

    # Remove extra spaces
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()
import openai
from app.utils.config_loader import CONFIG
from app.utils.logger import logger
openai.api_key = CONFIG["OPENAI_API_KEY"]

CLASSIFICATION_PROMPT = """
You are a classifier. Given the property listing text and details, answer with one label: {labels}.
Return only the label.

Listing text:
{listing_text}

Fields:
{fields}
"""

def classify_listing(listing_text: str, fields: dict, labels=["development", "not_development", "maybe"]):
    prompt = CLASSIFICATION_PROMPT.format(labels=", ".join(labels), listing_text=listing_text, fields=fields)
    try:
        resp = openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            max_tokens=8,
            temperature=0
        )
        label = resp.choices[0].text.strip().splitlines()[0]
        logger.info("OpenAI label: %s", label)
        return label
    except Exception as e:
        logger.exception("OpenAI classify error: %s", e)
        return "error"

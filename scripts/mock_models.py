"""Write src/deep_reasoning/web/mock_models.js: the OpenAI model names the model menu
lists in the settings round, from genai-prices' bundled data, until the menu reads each
provider's own GET /models.

Run from the repo root: uv run python scripts/mock_models.py
"""

import json
import re
from pathlib import Path

import structlog
from genai_prices.data_snapshot import get_snapshot

OUT = Path(__file__).resolve().parents[1] / "src/deep_reasoning/web/mock_models.js"
PROVIDER = "openai"
# Chat models only: OpenAI's list also has embeddings, speech, images and fine-tunes.
CHAT = re.compile(r"^(gpt-|o\d|chatgpt-|codex-)")
NOT_CHAT = re.compile(r"image|audio|realtime|transcribe|tts|search|research|live|ft")
HEADER = (
    "// Written by scripts/mock_models.py from genai-prices' data: the OpenAI models the"
    " model menu lists until it reads each provider's GET /models.\n"
)

log = structlog.get_logger()


def main():
    provider = get_snapshot().find_provider(None, PROVIDER, None)
    # An id the model's own matcher accepts is a name the API answers to.
    names = [
        model.id
        for model in provider.models
        if model.is_match(model.id)
        and CHAT.match(model.id)
        and not NOT_CHAT.search(model.id)
    ]
    OUT.write_text(f"{HEADER}export const OPENAI_MODELS = {json.dumps(names)};\n")
    log.info("Wrote the mock model list", file=str(OUT), models=len(names))


if __name__ == "__main__":
    main()

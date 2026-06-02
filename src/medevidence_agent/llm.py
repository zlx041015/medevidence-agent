import json
import time
from urllib import request

from medevidence_agent.config import Settings


def chat_completion(
    settings: Settings,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.2,
) -> str:
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY 未配置。")

    if not settings.openai_base_url:
        raise ValueError("OPENAI_BASE_URL 未配置。")

    if not settings.openai_model:
        raise ValueError("OPENAI_MODEL 未配置。")

    url = settings.openai_base_url.rstrip("/") + "/chat/completions"

    payload = {
        "model": settings.openai_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
    }

    data = json.dumps(payload).encode("utf-8")

    req = request.Request(
        url=url,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.openai_api_key}",
        },
    )

    last_error: Exception | None = None

    for attempt in range(3):
        try:
            with request.urlopen(req, timeout=60) as response:
                raw = response.read().decode("utf-8")

            result = json.loads(raw)
            return result["choices"][0]["message"]["content"]
        except Exception as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(1.2 * (attempt + 1))
            else:
                break

    raise RuntimeError(f"LLM request failed after 3 attempts: {last_error}")

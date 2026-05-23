import logging
import os
from groq import AsyncGroq
from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log

logger = logging.getLogger(__name__)

_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

MODEL   = "llama-3.3-70b-versatile"
TIMEOUT = int(os.getenv("LLM_TIMEOUT_SECONDS", 45))


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    before_sleep=before_sleep_log(logger, logging.WARNING),
)
async def call_llm(prompt: str) -> str:
    
    response = await _client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres un experto en ciberseguridad y análisis de redes IoT. "
                    "Tu tarea es interpretar resultados de clustering multivariado "
                    "aplicado a tráfico de red de dispositivos IoT para identificar "
                    "patrones de ciberataques. Sé preciso, técnico y estructurado."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,   # baja temperatura para análisis técnico consistente
        max_tokens=1500,
        timeout=TIMEOUT,
    )
    return response.choices[0].message.content
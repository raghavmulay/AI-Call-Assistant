import ollama
import time

SYSTEM_PROMPT = (
    "You are a college assistant. "
    "Reply in one short natural sentence only."
)

def generate_response(text: str) -> str:

    start = time.time()

    response = ollama.chat(
        model="phi3:mini",

        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],

        options={
            "num_predict": 20,
            "temperature": 0.3,
            "top_k": 20,
            "top_p": 0.7
        }
    )

    end = time.time()

    print(f"[LLM Time]: {end - start:.2f} seconds")

    return response["message"]["content"].strip()
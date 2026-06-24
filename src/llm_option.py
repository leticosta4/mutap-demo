import os


def llm_generate(prompt: str, llm: str = "gemini") -> str:
    if llm == "gemini":
        return _gemini_generate(prompt)
    elif llm == "ollama":
        return _ollama_generate(prompt)
    raise ValueError(f"Unknown LLM: {llm}")


def _gemini_generate(prompt: str) -> str:
    from google import genai

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    resp = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )
    if not resp.text:
        raise RuntimeError("Gemini returned empty response")
    return resp.text


def _ollama_generate(prompt: str) -> str:
    import requests

    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    model = os.environ.get("OLLAMA_MODEL", "codellama:7b-instruct")
    resp = requests.post(
        f"{host}/api/generate",
        json={"model": model, "prompt": prompt, "stream": False},
        timeout=120,
    )
    return resp.json()["response"]

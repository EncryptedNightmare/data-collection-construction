from groq import Groq


def get_client_with_key(api_key: str) -> Groq:
    """Returnér en Groq-klient for den givne API-nøgle."""
    if not api_key:
        raise RuntimeError("API key mangler!")
    return Groq(
        api_key=api_key,
        default_headers={"Groq-Model-Version": "latest"},
    )

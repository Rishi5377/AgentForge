import os
import json
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "memory", "settings.json")

def load_settings() -> dict:
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {"models": {}, "api_keys": {}, "general": {}}

def get_model_for_role(role_env_prefix: str, default_model: str, default_provider: str = 'groq', temperature: float = 0.0, max_tokens: int = 4000, stop_after_attempt: int = 4):
    settings = load_settings()
    
    # Try settings.json first, then env
    provider_key = f"{role_env_prefix.lower()}_provider"
    model_key = f"{role_env_prefix.lower()}_model"
    
    # If the user has configured Gemini for frontend/backend, make it the default fallback for all roles
    models_dict = settings.get("models", {})
    any_gemini = any(val == "gemini" for val in models_dict.values())
    
    fallback_provider = "gemini" if any_gemini else default_provider
    fallback_model = "gemini-3.1-flash-lite" if any_gemini else default_model
    
    provider = models_dict.get(provider_key) or os.getenv(f"{role_env_prefix}_PROVIDER", os.getenv("DEFAULT_PROVIDER", fallback_provider)).lower()
    model_name = models_dict.get(model_key) or os.getenv(f"{role_env_prefix}_MODEL", fallback_model)
    
    if provider == 'gemini':
        # Look for role-specific key first, then fallback
        api_key = settings.get("api_keys", {}).get("gemini") or os.getenv(f"GEMINI_API_KEY_{role_env_prefix}") or os.getenv("GEMINI_API_KEY")
        model = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=temperature,
            max_output_tokens=max_tokens,
            max_retries=stop_after_attempt
        )
        return model
    elif provider == 'openai' or provider == 'ollama' or provider == 'lmstudio':
        # OpenAI compatible
        api_key = settings.get("api_keys", {}).get("openai") or os.getenv(f"{role_env_prefix}_API_KEY", os.getenv("OPENAI_API_KEY", "not-needed-for-local"))
        base_url = os.getenv("OLLAMA_BASE_URL") if provider == 'ollama' else None
        return ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=stop_after_attempt
        )
    else:
        # Groq default
        api_key = settings.get("api_keys", {}).get("groq") or os.getenv(f"GROQ_KEY_{role_env_prefix}") or os.getenv("GROQ_API_KEY")
        return ChatGroq(
            model=model_name,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=stop_after_attempt
        )

def get_supervisor_model():
    return get_model_for_role("SUPERVISOR", "llama-3.3-70b-versatile", max_tokens=4000)

def get_database_model():
    return get_model_for_role("DB", "llama-3.3-70b-versatile", max_tokens=1500)

def get_backend_model():
    return get_model_for_role("BACKEND", "llama-3.3-70b-versatile", max_tokens=8192)

def get_frontend_model():
    return get_model_for_role("FRONTEND", "llama-3.3-70b-versatile", max_tokens=8192)

def get_assembler_model():
    return get_model_for_role("ASSEMBLER", "llama-3.3-70b-versatile", max_tokens=8192)

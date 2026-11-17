import os
import google.generativeai as genai
from langchain_core.embeddings import Embeddings
from features.apikeys import GEMINIAI_API_KEY, GEMINI_API_KEY

DEFAULT_GEMINI_MODEL = "gemini-3.5-flash-lite"
DEFAULT_EMBEDDING_MODEL = "models/gemini-embedding-001"

def configure_gemini(api_key=None):
    key = api_key or GEMINI_API_KEY or GEMINIAI_API_KEY or os.getenv("GOOGLE_API_KEY")
    if key:
        os.environ["GOOGLE_API_KEY"] = key
        genai.configure(api_key=key, transport="rest")
    return key

def get_gemini_model(model_name=DEFAULT_GEMINI_MODEL):
    configure_gemini()
    return genai.GenerativeModel(model_name)

def extract_gemini_text(response):
    if response is None:
        return ""
    try:
        return response.text
    except Exception:
        pass
    if hasattr(response, "candidates") and response.candidates:
        candidate = response.candidates[0]
        if hasattr(candidate, "content") and hasattr(candidate.content, "parts"):
            text_parts = [p.text for p in candidate.content.parts if hasattr(p, "text") and p.text]
            if text_parts:
                return "".join(text_parts)
    return ""

class GeminiRestEmbeddings(Embeddings):
    def __init__(self, model=DEFAULT_EMBEDDING_MODEL, api_key=None):
        self.model = model
        self.api_key = configure_gemini(api_key)

    def embed_documents(self, texts):
        configure_gemini(self.api_key)
        results = []
        for text in texts:
            res = genai.embed_content(model=self.model, content=text)
            results.append(res["embedding"])
        return results

    def embed_query(self, text):
        configure_gemini(self.api_key)
        res = genai.embed_content(model=self.model, content=text)
        return res["embedding"]

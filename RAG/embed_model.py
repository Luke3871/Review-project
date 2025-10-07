from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL_ID

_model = None

def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL_ID)
    return _model
"""
MLX Embedding Server — Ollama-compatible API for jina-code-embeddings-1.5b

Exposes POST /api/embeddings with the same contract as Ollama:
  Request:  {"model": "...", "prompt": "text"}
  Response: {"embedding": [float, ...]}

Usage:
  source .venv/bin/activate
  python server.py [--port 11435] [--dim 1024]
"""

import argparse
import json
import sys
import time
from pathlib import Path

import mlx.core as mx
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

MODEL_ID = "jinaai/jina-code-embeddings-1.5b-mlx"

# ── Load model at startup ──────────────────────────────────────────────────

def load_model():
    from huggingface_hub import snapshot_download
    from tokenizers import Tokenizer

    t0 = time.time()
    model_path = snapshot_download(MODEL_ID)
    sys.path.insert(0, model_path)
    from model import JinaCodeEmbeddingModel

    with open(Path(model_path) / "config.json") as f:
        config = json.load(f)

    model = JinaCodeEmbeddingModel(config)
    weights = mx.load(str(Path(model_path) / "model.safetensors"))
    model.load_weights(list(weights.items()))
    mx.eval(model.parameters())

    tokenizer = Tokenizer.from_file(str(Path(model_path) / "tokenizer.json"))
    print(f"[embedding-server] Model loaded in {time.time() - t0:.1f}s", file=sys.stderr)
    return model, tokenizer


MODEL, TOKENIZER = load_model()

# ── FastAPI app ────────────────────────────────────────────────────────────

app = FastAPI(title="MLX Embedding Server")


class EmbedRequest(BaseModel):
    model: str = ""
    prompt: str = ""


class EmbedResponse(BaseModel):
    embedding: list[float]


@app.post("/api/embeddings")
def embed(req: EmbedRequest) -> EmbedResponse:
    """Ollama-compatible embedding endpoint."""
    text = req.prompt.strip()
    if not text:
        return EmbedResponse(embedding=[0.0] * TRUNCATE_DIM)

    # Detect task type: code vs natural language query
    task = "code2code" if _looks_like_code(text) else "nl2code"
    prompt_type = "passage" if task == "code2code" else "query"

    emb = MODEL.encode(
        [text],
        TOKENIZER,
        task=task,
        prompt_type=prompt_type,
        truncate_dim=TRUNCATE_DIM,
    )
    mx.eval(emb)
    return EmbedResponse(embedding=emb[0].tolist())


@app.get("/api/tags")
def tags():
    """Ollama-compatible model list endpoint."""
    return {"models": [{"name": "jina-code-embeddings-1.5b", "size": "3GB"}]}


@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL_ID, "dimensions": TRUNCATE_DIM}


def _looks_like_code(text: str) -> bool:
    """Heuristic: if text contains common code patterns, treat as code passage."""
    code_signals = ("def ", "class ", "import ", "function ", "const ", "let ", "var ",
                    "async ", "await ", "return ", "self.", "this.", "=>", "->", "::", "();")
    return any(sig in text for sig in code_signals)


# ── Entry point ────────────────────────────────────────────────────────────

TRUNCATE_DIM = 1024  # default, overridden by --dim

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MLX Embedding Server")
    parser.add_argument("--port", type=int, default=11435, help="Port (default: 11435)")
    parser.add_argument("--dim", type=int, default=1024, help="Embedding dimension (default: 1024, max: 1536)")
    args = parser.parse_args()
    TRUNCATE_DIM = args.dim
    print(f"[embedding-server] Starting on port {args.port}, dim={TRUNCATE_DIM}", file=sys.stderr)
    uvicorn.run(app, host="0.0.0.0", port=args.port, log_level="warning")

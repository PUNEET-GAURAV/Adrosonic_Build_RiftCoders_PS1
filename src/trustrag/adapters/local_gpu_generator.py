import os
from typing import Sequence
import torch
from transformers import pipeline
from trustrag.core.models import ScoredPassage

class LocalGPUGenerator:
    def __init__(self, model_name: str = "HuggingFaceTB/SmolLM2-135M-Instruct"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        # Use bfloat16 or float32 for CPU to avoid very slow float16 ops
        dtype = torch.bfloat16 if self.device == "cpu" else torch.float16
        
        # Download and load the model on the GPU or CPU
        self.pipe = pipeline(
            "text-generation",
            model=model_name,
            device_map="auto" if self.device == "cuda" else None,
            torch_dtype=dtype,
            trust_remote_code=True,
        )

    def generate(self, query: str, passages: Sequence[ScoredPassage]) -> str | None:
        if not passages:
            return "I don't have enough context to answer that."

        # Truncate context to only the top 2 passages for speed
        context = "\n".join([f"[{i+1}] {p.text}" for i, p in enumerate(passages[:2])])
        
        messages = [
            {"role": "system", "content": "You are a strict AI assistant. Answer concisely using ONLY the provided context."},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
        ]
        
        try:
            outputs = self.pipe(messages, max_new_tokens=100, do_sample=False)
            return outputs[0]["generated_text"][-1]["content"].strip()
        except Exception as e:
            return f"(Error generating answer: {e})"

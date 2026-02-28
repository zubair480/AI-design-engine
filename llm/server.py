"""
vLLM inference server for Qwen models on Modal H100.

Runs as a long-lived background service.
Agents call this via Modal RPC, not HTTP.
"""

import subprocess
import modal
import time
from config import app, LLM_MODEL_ID, hf_secret, _add_local_sources

VLLM_PORT = 8000
MINUTES = 60
N_GPU = 1

# Cache volumes for model weights and vLLM internal cache
hf_cache_vol = modal.Volume.from_name("huggingface-cache", create_if_missing=True)
vllm_cache_vol = modal.Volume.from_name("vllm-cache", create_if_missing=True)

# Base image with vLLM pre-installed + local source code
vllm_image = _add_local_sources(
    modal.Image.from_registry("nvidia/cuda:12.8.0-devel-ubuntu22.04", add_python="3.12")
    .entrypoint([])
    .uv_pip_install(
        "vllm==0.13.0",
        "huggingface-hub==0.36.0",
        "httpx>=0.27",
    )
    .env({"HF_XET_HIGH_PERFORMANCE": "1"})  # faster model transfers
)


@app.function(
    image=vllm_image,
    gpu=f"H100:{N_GPU}",
    scaledown_window=15 * MINUTES,  # shutdown after 15 min of no requests
    timeout=30 * MINUTES,  # long timeout for first run (model download)
    secrets=[hf_secret],
    volumes={
        "/root/.cache/huggingface": hf_cache_vol,
        "/root/.cache/vllm": vllm_cache_vol,
    },
)
@modal.concurrent(max_inputs=32)
def serve():
    """Start vLLM OpenAI-compatible API server and keep it running."""
    cmd = [
        "vllm",
        "serve",
        "--uvicorn-log-level=info",
        LLM_MODEL_ID,
        "--served-model-name",
        "llm",
        "--host",
        "0.0.0.0",
        "--port",
        str(VLLM_PORT),
        "--enforce-eager",  # faster startup
        "--tensor-parallel-size",
        str(N_GPU),
    ]

    print(f"🚀 Starting vLLM server with command: {' '.join(cmd)}")
    process = subprocess.Popen(" ".join(cmd), shell=True)
    
    # Keep the function running by polling the process
    while True:
        if process.poll() is not None:
            # Process exited unexpectedly
            print(f"⚠️ vLLM process exited with code {process.returncode}")
            break
        time.sleep(5)


@app.cls(
    image=vllm_image,
    gpu=f"H100:{N_GPU}",
    scaledown_window=15 * MINUTES,
    timeout=30 * MINUTES,
    secrets=[hf_secret],
    volumes={
        "/root/.cache/huggingface": hf_cache_vol,
        "/root/.cache/vllm": vllm_cache_vol,
    },
)
@modal.concurrent(max_inputs=32)
class LlmServer:
    """vLLM server wrapper for Modal RPC calls."""
    
    @modal.enter()
    def startup(self):
        """Start the vLLM server process."""
        import time
        import subprocess
        
        cmd = [
            "vllm",
            "serve",
            "--uvicorn-log-level=info",
            LLM_MODEL_ID,
            "--served-model-name",
            "llm",
            "--host",
            "0.0.0.0",
            "--port",
            str(VLLM_PORT),
            "--enforce-eager",  # faster startup
            "--tensor-parallel-size",
            str(N_GPU),
        ]
        
        print(f"🚀 Starting vLLM server locally...")
        self.process = subprocess.Popen(" ".join(cmd), shell=True)
        
        # Wait for server to be ready (large models can take 5+ min to load weights)
        import httpx
        max_retries = 600
        for attempt in range(max_retries):
            try:
                with httpx.Client(timeout=5.0) as client:
                    response = client.get(f"http://localhost:{VLLM_PORT}/health")
                    if response.status_code == 200:
                        print(f"✅ vLLM server ready after {attempt}s!")
                        return
            except Exception:
                if attempt % 10 == 0:
                    print(f"⏳ Waiting for vLLM... ({attempt}s)")
                time.sleep(1)
        
        raise RuntimeError("vLLM server failed to start after 600 seconds")
    
    @modal.exit()
    def cleanup(self):
        """Kill the vLLM server when done."""
        if hasattr(self, 'process'):
            self.process.terminate()
    
    @modal.method()
    def generate(
        self,
        prompt: str,
        system_prompt: str = "You are a helpful AI assistant.",
        temperature: float = 0.3,
        max_tokens: int = 4096,
        json_mode: bool = False,
    ) -> str:
        """Generate text using vLLM via HTTP to localhost."""
        import httpx
        
        if json_mode:
            system_prompt += (
                "\n\nIMPORTANT: You MUST respond with valid JSON only. "
                "No markdown, no explanation, no code fences. Just raw JSON."
            )

        payload = {
            "model": "llm",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": 0.95 if temperature > 0 else 1.0,
        }
        
        try:
            with httpx.Client(timeout=300.0) as client:
                response = client.post(
                    f"http://localhost:{VLLM_PORT}/v1/chat/completions",
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Error calling vLLM: {e}")
            raise

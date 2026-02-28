#!/usr/bin/env python
"""
Quick setup & test script for the AI Decision Engine.

Usage:
  python quickstart.py
"""

import subprocess
import sys
import os


def run(cmd: str, description: str = ""):
    """Run a shell command and return success/failure."""
    print(f"\n{'='*60}")
    if description:
        print(f"  {description}")
    print(f"{'='*60}")
    print(f"  → {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=os.path.dirname(__file__))
    if result.returncode != 0:
        print(f"  ✗ FAILED (exit code {result.returncode})")
        return False
    print(f"  ✓ SUCCESS")
    return True


def main():
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║         🧠  AI DECISION ENGINE — QUICKSTART SETUP                         ║
║                                                                            ║
║  Autonomous Multi-Agent Business Analysis System                          ║
║  - 5,000 Monte Carlo simulations in 12 seconds                            ║
║  - Llama 3.1 70B reasoning engine on Modal H100                           ║
║  - Real-time React frontend with WebSocket updates                        ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

    steps = [
        ("c:/python313/python.exe -m pip install --upgrade pip", "Step 1: Upgrade pip"),
        ("c:/python313/python.exe -m pip install -r requirements.txt", "Step 2: Install Python dependencies"),
        ("modal token new", "Step 3: Authenticate with Modal (browser window will open)"),
        ("modal secret create huggingface-secret HUGGING_FACE_HUB_TOKEN=hf_YOUR_TOKEN", "Step 4: Store HuggingFace token (edit the command with your actual token)"),
    ]

    completed = 0
    for cmd, desc in steps:
        if "token new" in cmd or "secret create" in cmd:
            print(f"\n{'='*60}")
            print(f"  {desc}")
            print(f"{'='*60}")
            print(f"  ⚠️  MANUAL STEP")
            print(f"  → Run this command in your terminal:")
            print(f"     {cmd}")
            print()
            response = input("  Press ENTER when done, or type 'skip' to skip this step: ").strip()
            if response.lower() != "skip":
                completed += 1
        elif run(cmd, desc):
            completed += 1
        else:
            print(f"\n  ⚠️  Step failed. Please fix the issue and try again.")
            return 1

    print(f"""
{'='*60}
  ✓ SETUP COMPLETE
{'='*60}

Next steps:

1️⃣  TEST WITH CLI (no frontend):
    modal run app.py --prompt "Design a profitable coffee shop"

2️⃣  RUN WEB DEMO (with real-time frontend):
    modal serve app.py
    → Open the URL in your browser
    → Type a prompt and watch agents work in real-time
    → View profit distribution histogram
    → See AI-generated strategic analysis

3️⃣  DEPLOY TO PRODUCTION:
    modal deploy app.py
    → Your app gets a permanent public URL
    → Scales automatically based on demand
    → Pay only for compute used

Learn more:
  → Full docs: README.md
  → Modal docs: https://modal.com/docs
  → Watch demo video: (when available)
""")

    return 0


if __name__ == "__main__":
    sys.exit(main())

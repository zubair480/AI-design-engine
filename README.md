# 🏡 EstateAgent AI: Hyper-Local Real Estate Intelligence

**EstateAgent AI** is a high-performance, autonomous multi-agent swarm system designed to evaluate real estate investment opportunities across global regions in parallel. Built on a custom **Map-Reduce architecture**, it orchestrates a swarm of AI agents to deliver deep-dive, data-driven investment scores, strategic insights, and persistent contextual memory for complex follow-up analysis.

---

## 🧠 The Intelligence Engine

EstateAgent AI utilizes a sophisticated multi-model pipeline to ensure reliability and depth:

* **Primary Brain:** **Qwen 2.5 (7B-Instruct)** hosted via **vLLM on Modal (H100 GPUs)**. This serves as the Planner, Analyst Swarm node, and Conclusion Advisor.
* **Contextual Memory:** **Supermemory** acts as the persistent memory layer. It stores every analysis, regional insight, and user interaction, allowing the system to handle complex **follow-up questions** (e.g., *"How does this compare to the London report from last week?"*) without losing context.
* **Fail-Safe Routing:** **Llama 3.1 (8B & 70B)** running on **Cloudflare Workers AI** acts as a high-speed fallback for prompt classification and to mitigate cold starts.
* **Deployment & Scaling:** Hosted on **Aedify**, providing a streamlined, vertically-owned infrastructure for full-stack AI deployment and instant global scaling.

---

## 🚀 Key Features

* **⚡ Parallel Swarm Analysis:** Utilizes Modal’s container fan-out to spin up $N$ analysts simultaneously, processing massive datasets in seconds.
* **📍 Live Market Pulse:** Integrates directly with the **Redfin API** to fetch up-to-the-minute regional data, including median home values, listing trends, and rental yields.
* **🧠 Persistent Follow-ups:** Powered by **Supermemory**, the system remembers your investment history. You can ask follow-up questions across different sessions, and the AI will recall previous scores and data points.
* **📊 Standardized Scoring (The 100-Point Rubric):**
* **ROI Potential (0-50):** Profitability, appreciation, and local demand.
* **Feasibility (0-30):** Market entry ease, regulations, and zoning.
* **Risk Mitigation (0-20):** Downside protection and market volatility.


* **🌐 Real-Time Streaming UI:** A built-in frontend featuring live agent progress tracking, AI-generated strategic analysis, and profit distribution histograms.

---

## 🛠️ How it Works

1. **The Planner:** Receives the global objective (e.g., *"Find the best coffee shop locations in London"*) and deconstructs it into target regions.
2. **The Memory Check:** **Supermemory** is queried to see if similar regions or objectives have been analyzed recently, providing historical context to the Planner.
3. **The Orchestrator:** Python fetches live, up-to-date regional market data from the **Redfin API** for every identified region.
4. **The Swarm (Analyst Agents):** Parallel AI agents process local market data, evaluate feasibility, and generate structured JSON reports.
5. **The Synthesizer:** Aggregates swarm data into a visual dashboard and saves the state to **Supermemory** for future follow-up queries.

---

## 🚦 Getting Started

### Prerequisites

* Python 3.10+
* A [Modal](https://modal.com) account
* Aedify CLI (`npm install -g aedify`)
* Supermemory API Key
* Redfin API access credentials

### Installation

```bash
pip install modal
modal setup

```

### Usage

**1️⃣ Run Web Demo (Real-Time UI)**
Launch the interactive dashboard to watch the agents work, view profit histograms, and see live strategic analysis:

```bash
modal serve app.py

```

**2️⃣ Deploy to Production via Aedify**
Deploy the full-stack application to Aedify's AI-optimized infrastructure:

```bash
aedify deploy

```

**3️⃣ Test Follow-up Intelligence**
Once deployed, you can ask questions like:

> "Compare the yield of the top 3 regions to the report I ran yesterday."
> *(Supermemory will automatically retrieve the historical data to formulate the answer.)*

---

## 📉 Scoring Methodology

| Category | Weight | Focus Area |
| --- | --- | --- |
| **ROI Potential** | 50 pts | Yield, Appreciation, Local Demand |
| **Feasibility** | 30 pts | Regulations, Zoning, Development Cost |
| **Risk Mitigation** | 20 pts | Market Saturation, Economic Stability |

---

## 🧰 Tech Stack

| Component | Technology |
| --- | --- |
| **Deployment** | **Aedify** (AI-Native Infrastructure) |
| **Memory** | **Supermemory** (Persistent Context & Follow-ups) |
| **Compute** | Modal (Serverless H100s / CPUs) |
| **Data Source** | **Redfin API** (Real-time Real Estate Data) |
| **LLMs** | Qwen 2.5, Llama 3.1 |

---

## 📝 AI Disclosure & Credits

In compliance with hackathon transparency requirements, the following AI tools and models were used:

* **Development Aides:** **GitHub Copilot** was used for boilerplate code and CSS scaffolding.
* **Ideation:** **Gemini 1.5 Pro**, **ChatGPT**, and **Claude** assisted in brainstorming complex mathematical formulas (Monte Carlo simulations) and refining documentation.
* **Infrastructure:** The multi-agent Map-Reduce architecture and streaming infrastructure were custom-architected to leverage the strengths of Aedify and Modal.

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](https://www.google.com/search?q=LICENSE) file for details.

---

*Generated by EstateAgent AI — Hyper-local data. Global perspective.*


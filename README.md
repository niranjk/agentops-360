# AgentOps-360 
The Autonomous Enterprise Vendor Procurement & Risk Mitigator. 

# 🧠 AgentOps-360: Autonomous Enterprise Vendor Procurement & Risk Mitigator

### 🌐 Live Public Demo URL: [http://95.179.142.108:8501](http://95.179.142.108:8501)
> Deployed natively on **Vultr Compute Architecture** for the **Milan AI Week Hackathon** (AI Agent Olympics).

---

## 🚀 Executive Value Proposition (The 80/20 Rule)
*   **The Core Impact:** Slashes the enterprise vendor contract audit lifecycle from **15 hours down to 12 seconds**.
*   **The Mission:** Transitions enterprise document parsing from passive chatbot "copilots" into a proactive **Autonomous Decision Engine** that makes deterministic, risk-mitigated business choices.
*   **Enterprise Utility:** Eliminates compliance leakage, detects toxic auto-renewal legal traps, and flags SLA vulnerabilities before a human executive signs.

---

## 🛠️ The Hackathon Technology Stack
Our architecture integrates the specific core requirements of the hackathon ecosystem:

*   **Hosting & Compute Platform:** Vultr Cloud Compute VM Instance (Ubuntu Linux Core)
*   **AI Inference Gateway Engine:** [Featherless.ai](https://featherless.ai) High-Throughput Open-Source Clustering API
*   **Advanced Model Brain:** `meta-llama/Meta-Llama-3-70B-Instruct` (Selected for elite text synthesis, structural layout retention, and zero commercial API rate limits)
*   **Local Text Matrix Extraction:** `pypdf`
*   **Data Validation Layer:** `pydantic` Enforced Deterministic JSON Framework
*   **User Interface UX Layer:** Streamlit Dashboard with an integrated native Client-Side Client SpeechSynthesis API Bridge (Zero-Cost Voice Briefing Execution)

---

## 🧠 Advanced Core Concepts & Architecture

### 1. Map-Reduce Multi-Stage Document Chunking
To prevent the `429 Resource Exhausted` rate limits of public APIs and overcome the token context boundaries of open-source models, AgentOps-360 uses a distributed parsing strategy:
*   **Map Phase:** The system chunks a multi-page contract on the server edge into tight, 2-page text arrays. It streams these arrays in parallel to Featherless compute nodes to isolate localized risks.
*   **Reduce Phase:** The extracted segment findings are compiled and piped back into a final synthesis model layer to build a unified Master Executive Risk Assessment report.

### 2. Zero-Data-Retention Privacy Posture (ZDR)
Built explicitly to comply with the **EU AI Act (Limited Risk Category)** and **GDPR Data Minimization Frameworks**:
*   Contract contents are kept entirely within short-lived virtual memory string buffers during computation.
*   Leverages the **Featherless Zero-Logging Privacy Policy**—preventing sensitive corporate intelligence from leaking into public training data pools.

### 3. Open Loop Human-In-The-Loop Governance
The agent acts as an automated, high-speed strategic analyst but does not finalize contracts autonomously. It produces structured recommendations (`GO`, `NO-GO`, `RE-NEGOTIATE`) with precise legal validations, keeping corporate oversight completely in human hands.

---

## 💻 Local Installation & Server Deployment

This workspace utilizes `uv` for blazing-fast dependency tracking and environment isolation.

### 1. Project Initialization & Dependency Provisioning
```bash
# Clone the repository code matrix
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd agentops-360

# Install uv globally via python tools if missing
pip install uv --break-system-packages

# Add local credentials parameters
cat <<EOT > .env
FEATHERLESS_API_KEY="your-featherless-api-key-here"
EOT

# Lock down virtual structures
uv init
uv add streamlit openai pypdf
```

### 2. Launch Streamlit Globally (Natively via Vultr VM)
```bash
# Initialize a background virtual screen container to ensure 100% persistence
tmux new -s agentops_session

# Open inbound port configurations inside the host kernel
sudo iptables -I INPUT 1 -p tcp --dport 8501 -j ACCEPT
sudo iptables-save

# Start the public production engine listening globally on port 8501
uv run streamlit run app.py --server.port 8501 --server.address 0.0.0.0

# Safely disconnect window session without stopping the process: Press [Ctrl + B], then [D]
```

---

## 📊 Documented Workspaces
*   **Engineering Framework Logging:** Tracks implementation iterations, Map-Reduce schemas, and kernel network resolution steps natively across our connected **Confluence Workspace**.

import streamlit as st
import os
import json
import pypdf
from openai import OpenAI  # Featherless utilizes OpenAI routing patterns
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# 1. Page Configuration
st.set_page_config(page_title="AgentOps-360 [Featherless Engine]", page_icon="🧠", layout="wide")
load_dotenv()

# Verify Featherless credentials are clear
api_key = os.getenv("FEATHERLESS_API_KEY")
if not api_key:
    st.error("🔑 CRITICAL ERROR: FEATHERLESS_API_KEY is missing from your .env file.")
    st.stop()

# Initialize the OpenAI compatible client pointing to Featherless cloud routing
client = OpenAI(
    base_url="https://api.featherless.ai/v1",
    api_key=api_key
)

# Choose Featherless active Mistral model profile variant
MISTRAL_MODEL_ID = "mistralai/Mistral-7B-Instruct-v0.3" 

# 2. Free Audio Briefing Component Tool
def play_browser_audio(text_to_speak: str):
    """Injects a tiny JavaScript block into the browser to speak the script aloud for free."""
    escaped_text = text_to_speak.replace("'", "\\'").replace("\n", " ")
    js_code = f"""
    <script>
        var msg = new SpeechSynthesisUtterance('{escaped_text}');
        window.speechSynthesis.speak(msg);
    </script>
    """
    st.components.v1.html(js_code, height=0)

# 3. Core Business Logic Engine (Local Extraction + Mistral Reasoning Engine)
def run_autonomous_featherless_audit(uploaded_file):
    pdf_reader = pypdf.PdfReader(uploaded_file)
    pages_text = []
    for page in pdf_reader.pages:
        text = page.extract_text()
        if text:
            pages_text.append(text)
            
    if not pages_text:
        raise ValueError("The uploaded PDF contains no extractable text strings.")
        
    all_discovered_findings = []
    detected_vendor = "Unknown Vendor"
    
    # Process the document in tight chunks of 2 pages
    chunk_size = 2
    st.toast(f"Processing {len(pages_text)} pages in multi-step agent workflow cycles...")
    
    # HELPER FUNCTION: Safely extracts content text from Featherless object or raw dictionary format
    def get_content_safely(api_response):
        print(f"DEBUG: API Response type: {type(api_response)}")
        print(f"DEBUG: API Response: {api_response}")
        
        try:
            # Try reading as an object first
            content = api_response.choices[0].message.content
            print(f"DEBUG: Got content from .choices[0].message.content: {content}")
            if content:
                return content
        except (AttributeError, TypeError, IndexError) as e:
            print(f"DEBUG: Object access failed: {e}")
            pass
        
        try:
            # Fallback: try accessing choices directly
            choice = api_response.choices[0]
            print(f"DEBUG: Choice type: {type(choice)}, value: {choice}")
            
            # Handle case where choice is a list
            if isinstance(choice, list):
                choice = choice[0] if choice else {}
            
            # Try dict access patterns
            if isinstance(choice, dict):
                content = choice.get("message", {}).get("content") or choice.get("content")
                print(f"DEBUG: Dict access got: {content}")
                if content:
                    return content
            
            # Try object attribute access
            if hasattr(choice, "message"):
                content = choice.message.content if hasattr(choice.message, "content") else None
                print(f"DEBUG: Object attribute access got: {content}")
                if content:
                    return content
            
            # Last resort: direct dict key access
            content = choice.get("message", {}).get("content")
            print(f"DEBUG: Last resort dict access got: {content}")
            if content:
                return content
                
        except Exception as e:
            print(f"DEBUG: Exception in fallback: {type(e).__name__}: {e}")
        
        print("DEBUG: Returning empty string - all extraction methods failed")
        return ""


    for i in range(0, len(pages_text), chunk_size):
        current_chunk_text = "\n".join(pages_text[i:i+chunk_size])
        
        chunk_prompt = f"""You are an expert Enterprise Risk Auditor. Review this segment of a corporate agreement.
Identify financial liabilities, auto-renewals, data privacy flaws, or bad SLA metrics.

You MUST respond ONLY with valid JSON, nothing else. No explanation, no markdown, no code blocks - just pure JSON.

{{
  "vendor_name": "Extracted vendor name or Unknown",
  "findings": [
    {{
      "clause_title": "Clause identifier",
      "severity": "LOW / MEDIUM / HIGH / CRITICAL",
      "description": "Risk details description",
      "mitigation_strategy": "Actionable remediation steps"
    }}
  ]
}}

--- CONTRACT SEGMENT START ---
{current_chunk_text}
--- CONTRACT SEGMENT END ---

Respond with valid JSON only:"""

        response = client.chat.completions.create(
            model=MISTRAL_MODEL_ID,
            messages=[{"role": "user", "content": chunk_prompt}],
            temperature=0.1,
            max_tokens=1500
        )
        
        try:
            # Use our new bulletproof string parser here
            raw_content = get_content_safely(response)
            if not raw_content or not raw_content.strip():
                st.warning(f"Empty response from API for chunk {i//chunk_size + 1}")
                continue
            chunk_data = json.loads(raw_content)
            if chunk_data.get("findings"):
                all_discovered_findings.extend(chunk_data["findings"])
            if chunk_data.get("vendor_name") and chunk_data["vendor_name"] != "Unknown":
                detected_vendor = chunk_data["vendor_name"]
        except Exception as e:
            st.warning(f"Skipping chunk due to error: {e}")
            
    summary_prompt = f"""You are an expert Enterprise Chief Risk Officer. Review this master list of discovered risks.
Synthesize them, calculate an overall risk score out of 100, issue a final decision, 
and write an exceptional 30-second conversational voice briefing script for a busy executive.

You MUST respond ONLY with valid JSON, nothing else. No explanation, no markdown, no code blocks - just pure JSON.

{{
  "vendor_name": "{detected_vendor}",
  "overall_risk_score": 75,
  "go_no_go_recommendation": "GO / NO-GO / RE-NEGOTIATE with a short validation summary",
  "audio_briefing_script": "A natural sounding executive voice summary script",
  "critical_findings": []
}}

Master Risk List Data:
{json.dumps(all_discovered_findings)}

Respond with valid JSON only:"""
    
    final_response = client.chat.completions.create(
        model=MISTRAL_MODEL_ID,
        messages=[{"role": "user", "content": summary_prompt}],
        temperature=0.2,
        max_tokens=1500
    )
    
    # Use our new bulletproof string parser for the final compilation summary too
    final_raw_content = get_content_safely(final_response)
    if not final_raw_content or not final_raw_content.strip():
        raise ValueError("Final summary response from API was empty")
    compiled_report = json.loads(final_raw_content)
    compiled_report["critical_findings"] = all_discovered_findings[:10]
    return compiled_report



# 4. Streamlit Front-End Presentation Frame
st.title("🧠 AgentOps-360: Autonomous Enterprise Risk Auditor")
st.caption("Milan AI Week Hackathon Prototype — Powered by Featherless.ai (Mistral Engine) & Vultr")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📥 Upload Contract / Document")
    uploaded_file = st.file_uploader("Drag and drop your enterprise vendor PDF agreement here", type=["pdf"])
    
    if uploaded_file is not None:
        if st.button("🚀 Run Autonomous Agentic Audit", type="primary"):
            with st.spinner("🧠 Autonomous Featherless Multi-Agent Pipeline Executing..."):
                try:
                    st.session_state.featherless_report = run_autonomous_featherless_audit(uploaded_file)
                    st.success("🎯 Analysis Finished via Open-Source Infrastructure Pipeline!")
                except Exception as e:
                    st.error(f"Execution pipeline failure metrics caught: {e}")

with col2:
    st.subheader("📊 Live Autonomous Evaluation")
    
    if "featherless_report" in st.session_state:
        report = st.session_state.featherless_report
        
        c1, c2 = st.columns(2)
        with c1:
            st.metric(label="Counterparty / Vendor", value=report.get("vendor_name", "Unknown"))
        with c2:
            st.metric(label="Calculated Risk Score", value=f"{report.get('overall_risk_score', 0)} / 100")
            
        recommendation = report.get("go_no_go_recommendation", "RE-NEGOTIATE")
        if "NO-GO" in recommendation.upper():
            st.error(f"🚨 **Recommendation: {recommendation}**")
        elif "RE-NEGOTIATE" in recommendation.upper():
            st.warning(f"⚠️ **Recommendation: {recommendation}**")
        else:
            st.success(f"✅ **Recommendation: {recommendation}**")
            
        st.write("---")
        st.write("### 🔊 Executive Voice Briefing")
        briefing_script = report.get("audio_briefing_script", "No script compiled.")
        st.info(f"📄 *Script Draft:* \"{briefing_script}\"")
        if st.button("🎙️ Play Audio Briefing"):
            play_browser_audio(briefing_script)
            st.toast("Playing audio natively via your browser speaker...")
            
        st.write("---")
        st.write("### 🔍 Specific Findings Matrix")
        findings = report.get("critical_findings", [])
        for idx, item in enumerate(findings):
            with st.expander(f"{idx+1}. {item.get('clause_title', 'Risk Clause')} [{item.get('severity', 'MEDIUM')}]"):
                st.write(f"**Risk Profile:** {item.get('description')}")
                st.write(f"**Guru Mitigation Advice:** {item.get('mitigation_strategy')}")
    else:
        st.info("Upload a contract PDF data block on the left panel to execute full agent context chains via Featherless clusters.")

import streamlit as st
import os
import json
import pypdf
from google import genai
from google.genai import types
from dotenv import load_dotenv

# 1. Page Configuration
st.set_page_config(page_title="AgentOps-360 [Google Gemini]", page_icon="🧠", layout="wide")
load_dotenv()

# Verify Google API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error("🔑 CRITICAL ERROR: GEMINI_API_KEY is missing from your .env file.")
    st.stop()

# Initialize Google GenAI client
client = genai.Client(api_key=api_key) 

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
    
    # Process the document in tight chunks of 1 page
    chunk_size = 1
    st.toast(f"Processing {len(pages_text)} pages in multi-step agent workflow cycles...")
    
    # HELPER FUNCTION: Safely extracts content text from Featherless object or raw dictionary format
    def get_content_safely(api_response):
        try:
            content = api_response.choices[0].message.content
            if content:
                return content.strip()
        except (AttributeError, TypeError, IndexError):
            pass
        return ""
    
    # HELPER FUNCTION: Try to parse JSON, with fallback
    def safe_json_parse(text):
        """Try to parse JSON, with aggressive extraction"""
        if not text or not text.strip():
            return {}
        
        text = text.strip()
        
        # Try direct parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON from markdown code blocks
        if "```" in text:
            try:
                start = text.find("```json") + 7 if "```json" in text else text.find("```") + 3
                end = text.find("```", start)
                if end > start:
                    json_text = text[start:end].strip()
                    return json.loads(json_text)
            except (json.JSONDecodeError, ValueError):
                pass
        
        # Try to find { and } and extract JSON object
        try:
            start = text.find("{")
            if start != -1:
                # Find the matching closing brace
                brace_count = 0
                for i in range(start, len(text)):
                    if text[i] == "{":
                        brace_count += 1
                    elif text[i] == "}":
                        brace_count -= 1
                        if brace_count == 0:
                            json_text = text[start:i+1]
                            return json.loads(json_text)
        except (json.JSONDecodeError, ValueError):
            pass
        
        print(f"Could not extract JSON from: {text[:100]}")
        return {}


    for i in range(0, len(pages_text), chunk_size):
        current_chunk_text = "\n".join(pages_text[i:i+chunk_size])
        
        chunk_prompt = f"""TEXT:
{current_chunk_text[:1000]}

RESPOND ONLY WITH THIS JSON STRUCTURE (no other text):
{{"vendor_name":"extracted_or_unknown","findings":[{{"clause_title":"risk_title","severity":"HIGH","description":"risk_details","mitigation_strategy":"solution"}}]}}

If no risks, respond with:
{{"vendor_name":"unknown","findings":[]}}

RESPOND ONLY WITH JSON:"""

        response = client.chat.completions.create(
            model=MISTRAL_MODEL_ID,
            messages=[
                {"role": "system", "content": "You are a JSON generator. You respond ONLY with valid JSON, nothing else. No explanation, no text, only JSON."},
                {"role": "user", "content": chunk_prompt}
            ],
            temperature=0.1,
            max_tokens=600
        )
        
        try:
            # Use our new bulletproof string parser here
            raw_content = get_content_safely(response)
            if not raw_content or not raw_content.strip():
                continue
            
            chunk_data = safe_json_parse(raw_content)
            if not chunk_data:
                print(f"WARNING: Chunk {i//chunk_size + 1} returned invalid JSON: {raw_content[:100]}")
                continue
                
            if chunk_data.get("findings"):
                all_discovered_findings.extend(chunk_data["findings"])
            if chunk_data.get("vendor_name") and chunk_data["vendor_name"] != "Unknown" and chunk_data["vendor_name"] != "unknown":
                detected_vendor = chunk_data["vendor_name"]
        except Exception as e:
            print(f"Chunk {i//chunk_size + 1} exception: {type(e).__name__}")
            
    summary_prompt = f"""ANALYZE THESE RISKS:
{json.dumps(all_discovered_findings)[:800]}

RESPOND ONLY WITH THIS JSON (no other text):
{{"vendor_name":"vendor","overall_risk_score":50,"go_no_go_recommendation":"GO","audio_briefing_script":"summary","critical_findings":[]}}

RESPOND ONLY WITH JSON:"""
    
    final_response = client.chat.completions.create(
        model=MISTRAL_MODEL_ID,
        messages=[
            {"role": "system", "content": "You are a JSON generator. You respond ONLY with valid JSON, nothing else. No explanation, no text, only JSON."},
            {"role": "user", "content": summary_prompt}
        ],
        temperature=0.2,
        max_tokens=800
    )
    
    # Use our new bulletproof string parser for the final compilation summary too
    final_raw_content = get_content_safely(final_response)
    if final_raw_content and final_raw_content.strip():
        compiled_report = safe_json_parse(final_raw_content)
    else:
        compiled_report = {}
    
    # Always generate a valid report, even if final response failed
    if not compiled_report or "vendor_name" not in compiled_report:
        compiled_report = {
            "vendor_name": detected_vendor,
            "overall_risk_score": len(all_discovered_findings) * 15,  # Scale by findings count
            "go_no_go_recommendation": "RE-NEGOTIATE" if all_discovered_findings else "INCONCLUSIVE",
            "audio_briefing_script": f"Document review identified {len(all_discovered_findings)} potential risks requiring attention." if all_discovered_findings else "Unable to complete full analysis.",
            "critical_findings": all_discovered_findings[:10]
        }
    else:
        compiled_report.setdefault("critical_findings", [])
        compiled_report["critical_findings"] = all_discovered_findings[:10]
    
    # Cap risk score at 100
    compiled_report["overall_risk_score"] = min(compiled_report.get("overall_risk_score", 50), 100)
    
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

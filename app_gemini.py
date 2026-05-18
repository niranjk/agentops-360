import streamlit as st
import os
import json
import pypdf
from google import genai
from dotenv import load_dotenv

# 1. Page Configuration
st.set_page_config(page_title="AgentOps-360 [Gemini]", page_icon="🧠", layout="wide")
load_dotenv()

# Verify Google API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error("🔑 CRITICAL ERROR: GEMINI_API_KEY is missing from your .env file.")
    st.stop()

# Initialize Google GenAI client
client = genai.Client(api_key=api_key)

# 2. Audio Briefing Tool
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

# 3. Helper functions
def safe_json_parse(text):
    """Try to parse JSON with fallback extraction"""
    if not text or not text.strip():
        return {}
    
    text = text.strip()
    
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Try to extract from markdown
    if "```" in text:
        try:
            start = text.find("```json") + 7 if "```json" in text else text.find("```") + 3
            end = text.find("```", start)
            if end > start:
                return json.loads(text[start:end].strip())
        except:
            pass
    
    # Try to find JSON object
    try:
        start = text.find("{")
        if start != -1:
            brace_count = 0
            for i in range(start, len(text)):
                if text[i] == "{":
                    brace_count += 1
                elif text[i] == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        return json.loads(text[start:i+1])
    except:
        pass
    
    return {}

# 4. Main audit function
def run_contract_audit(uploaded_file):
    pdf_reader = pypdf.PdfReader(uploaded_file)
    pages_text = []
    for page in pdf_reader.pages:
        text = page.extract_text()
        if text:
            pages_text.append(text)
            
    if not pages_text:
        raise ValueError("PDF contains no extractable text")
        
    all_findings = []
    vendor_name = "Unknown Vendor"
    
    st.toast(f"Analyzing {len(pages_text)} pages...")
    progress_bar = st.progress(0)
    
    # Analyze each page
    for idx, page_text in enumerate(pages_text[:10]):
        progress_bar.progress((idx + 1) / min(11, len(pages_text) + 1))
        
        try:
            prompt = f"""Analyze this contract page for business risks. Return ONLY valid JSON:

CONTRACT TEXT:
{page_text[:2000]}

RETURN ONLY THIS JSON FORMAT (no other text):
{{"vendor_name":"vendor_or_unknown","findings":[{{"clause_title":"risk title","severity":"HIGH","description":"risk details","mitigation_strategy":"solution"}}]}}

If no risks found:
{{"vendor_name":"unknown","findings":[]}}"""

            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
            )
            
            data = safe_json_parse(response.text)
            if data and data.get("findings"):
                all_findings.extend(data["findings"])
            if data and data.get("vendor_name") and data["vendor_name"] != "unknown":
                vendor_name = data["vendor_name"]
                
        except Exception as e:
            st.warning(f"Page {idx + 1} processing skipped")
            continue
    
    # Generate final summary
    try:
        summary_prompt = f"""Based on these contract risks, generate final analysis. Return ONLY valid JSON:

RISKS:
{json.dumps(all_findings)[:1000]}

RETURN ONLY THIS JSON:
{{"vendor_name":"{vendor_name}","overall_risk_score":50,"go_no_go_recommendation":"GO","audio_briefing_script":"30-second summary of risks","critical_findings":[]}}"""

        final_response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=summary_prompt,
        )
        
        final_data = safe_json_parse(final_response.text)
        if final_data and "vendor_name" in final_data:
            final_data["critical_findings"] = all_findings[:10]
            return final_data
    except:
        pass
    
    # Fallback response
    return {
        "vendor_name": vendor_name,
        "overall_risk_score": min(len(all_findings) * 12, 100),
        "go_no_go_recommendation": "RE-NEGOTIATE" if all_findings else "INCONCLUSIVE",
        "audio_briefing_script": f"Found {len(all_findings)} contract risks requiring review.",
        "critical_findings": all_findings[:10]
    }

# 5. UI Layout
st.title("🧠 AgentOps-360: Contract Risk Auditor")
st.caption("Powered by Google Gemini 2.0 Flash")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📥 Upload Contract")
    uploaded_file = st.file_uploader("Upload PDF contract", type=["pdf"])
    
    if uploaded_file is not None:
        if st.button("🚀 Run Audit", type="primary"):
            with st.spinner("Processing contract..."):
                try:
                    report = run_contract_audit(uploaded_file)
                    st.session_state.report = report
                    st.success("Analysis complete!")
                except Exception as e:
                    st.error(f"Error: {e}")

with col2:
    st.subheader("📊 Risk Analysis")
    
    if "report" in st.session_state:
        report = st.session_state.report
        
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Vendor", report.get("vendor_name", "Unknown"))
        with c2:
            st.metric("Risk Score", f"{report.get('overall_risk_score', 0)}/100")
        
        rec = report.get("go_no_go_recommendation", "RE-NEGOTIATE")
        if "NO-GO" in rec.upper():
            st.error(f"🚨 {rec}")
        elif "RE-NEGOTIATE" in rec.upper():
            st.warning(f"⚠️ {rec}")
        else:
            st.success(f"✅ {rec}")
        
        st.write("---")
        st.write("### 🔊 Executive Summary")
        script = report.get("audio_briefing_script", "No summary available.")
        st.info(f'"{script}"')
        
        if st.button("🎙️ Play Audio"):
            play_browser_audio(script)
            st.toast("Playing audio...")
        
        st.write("---")
        st.write("### 🔍 Key Findings")
        findings = report.get("critical_findings", [])
        
        if findings:
            for idx, item in enumerate(findings, 1):
                with st.expander(f"{idx}. {item.get('clause_title', 'Risk')} [{item.get('severity', 'MEDIUM')}]"):
                    st.write(f"**Risk:** {item.get('description')}")
                    st.write(f"**Mitigation:** {item.get('mitigation_strategy')}")
        else:
            st.info("No major risks identified.")
    else:
        st.info("Upload a contract to begin analysis.")

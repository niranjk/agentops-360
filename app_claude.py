import streamlit as st
import os
import json
import pypdf
from openai import OpenAI
from dotenv import load_dotenv

# 1. Page Configuration
st.set_page_config(page_title="AgentOps-360 [Featherless]", page_icon="🧠", layout="wide")
load_dotenv()

# Verify Featherless credentials
api_key = os.getenv("FEATHERLESS_API_KEY")
if not api_key:
    st.error("🔑 CRITICAL ERROR: FEATHERLESS_API_KEY is missing from your .env file.")
    st.stop()

# Initialize Featherless client
client = OpenAI(
    base_url="https://api.featherless.ai/v1",
    api_key=api_key
)

# Use Claude model - best for JSON output
MODEL_ID = "anthropic/claude-3-5-sonnet"

# 2. Audio Briefing Tool
def play_browser_audio(text_to_speak: str):
    """Play audio briefing via browser"""
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
    
    st.toast(f"Analyzing {len(pages_text)} pages with Claude...")
    progress_bar = st.progress(0)
    
    # Analyze each page
    for idx, page_text in enumerate(pages_text[:10]):
        progress_bar.progress((idx + 1) / min(11, len(pages_text) + 1))
        
        try:
            prompt = f"""Analyze this contract page for business risks. Return ONLY valid JSON with no other text:

CONTRACT TEXT:
{page_text[:2000]}

Return ONLY this JSON format:
{{"vendor_name":"vendor_name_or_unknown","findings":[{{"clause_title":"risk_title","severity":"HIGH/MEDIUM/LOW/CRITICAL","description":"risk_details","mitigation_strategy":"solution"}}]}}

If no risks found, respond with:
{{"vendor_name":"unknown","findings":[]}}

RESPOND WITH ONLY JSON:"""

            response = client.chat.completions.create(
                model=MODEL_ID,
                messages=[
                    {"role": "system", "content": "You are a JSON generator. Respond ONLY with valid JSON, nothing else."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=800
            )
            
            raw_content = response.choices[0].message.content
            data = safe_json_parse(raw_content)
            
            if data and data.get("findings"):
                all_findings.extend(data["findings"])
            if data and data.get("vendor_name") and data["vendor_name"] != "unknown":
                vendor_name = data["vendor_name"]
                
        except Exception as e:
            print(f"Page {idx + 1} error: {e}")
            continue
    
    # Generate final summary
    try:
        summary_prompt = f"""You are a Chief Risk Officer. Analyze these contract risks and respond ONLY with JSON:

RISKS FOUND:
{json.dumps(all_findings)[:1200]}

Respond ONLY with this JSON:
{{"vendor_name":"{vendor_name}","overall_risk_score":50,"go_no_go_recommendation":"GO","audio_briefing_script":"Executive summary of risks","critical_findings":[]}}

RESPOND WITH ONLY JSON:"""

        final_response = client.chat.completions.create(
            model=MODEL_ID,
            messages=[
                {"role": "system", "content": "You are a JSON generator. Respond ONLY with valid JSON, nothing else."},
                {"role": "user", "content": summary_prompt}
            ],
            temperature=0.2,
            max_tokens=800
        )
        
        final_content = final_response.choices[0].message.content
        final_data = safe_json_parse(final_content)
        
        if final_data and "vendor_name" in final_data:
            final_data["critical_findings"] = all_findings[:10]
            return final_data
    except Exception as e:
        print(f"Final summary error: {e}")
    
    # Fallback response
    return {
        "vendor_name": vendor_name,
        "overall_risk_score": min(len(all_findings) * 12, 100),
        "go_no_go_recommendation": "RE-NEGOTIATE" if all_findings else "INCONCLUSIVE",
        "audio_briefing_script": f"Found {len(all_findings)} contract risks requiring attention.",
        "critical_findings": all_findings[:10]
    }

# 5. UI Layout
st.title("🧠 AgentOps-360: Contract Risk Auditor")
st.caption("Powered by Featherless.ai + Claude 3.5 Sonnet")

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
                    st.success("✅ Analysis complete!")
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

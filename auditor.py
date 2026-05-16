import os
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from dotenv import load_dotenv

# 1. Load environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("CRITICAL ERROR: GEMINI_API_KEY is missing from your .env file.")

# 2. Define the exact structured schema we want from the Agent
class RiskItem(BaseModel):
    clause_title: str = Field(description="Name of the high-risk clause found.")
    severity: str = Field(description="Severity levels: LOW, MEDIUM, HIGH, CRITICAL.")
    description: str = Field(description="Explanation of why this clause presents an enterprise risk.")
    mitigation_strategy: str = Field(description="Actionable advice for the manager to counter this risk.")

class AuditReport(BaseModel):
    vendor_name: str = Field(description="Extracted name of the vendor or counterparty.")
    overall_risk_score: int = Field(description="A calculated risk score out of 100.")
    critical_findings: list[RiskItem] = Field(description="List of discovered specific risk clauses.")
    go_no_go_recommendation: str = Field(description="A definitive decision: GO, NO-GO, or RE-NEGOTIATE with a short justification.")

# 3. Initialize the native Google GenAI Client
client = genai.Client(api_key=api_key)

def run_auditor(pdf_path: str) -> AuditReport:
    print(f"🔄 Ingesting and auditing: {pdf_path}...")
    
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Error: Could not find document at {pdf_path}")
        
    # 4. Upload document directly to the Gemini File API (Handles multi-page reports natively)
    print("📤 Uploading document to Gemini Context Engine...")
    uploaded_file = client.files.upload(file=pdf_path)
    
    prompt = """
    You are an expert Enterprise Risk Auditor and Legal Counsel. Analyze the attached document thoroughly.
    Identify any financial liabilities, sneaky auto-renewals, ambiguous SLAs, data privacy risks, or unfavorable termination clauses.
    Provide your output strictly adhering to the requested JSON schema. Do not include conversational text outside the JSON structure.
    """
    
    print("🧠 Processing with Gemini 2.0 Flash (Reasoning Engine)...")
    # Using gemini-2.0-flash for deep reasoning and multi-page text handling
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents=[uploaded_file, prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=AuditReport,
            temperature=0.1 # Low temperature for accurate compliance auditing
        ),
    )
    
    # Clean up file from the cloud after processing
    client.files.delete(name=uploaded_file.name)
    
    # Parse into the Pydantic model for complete system type-safety
    return AuditReport.model_validate_json(response.text)

if __name__ == "__main__":
    # Test file execution hook
    import sys
    if len(sys.argv) < 2:
        print("❌ Usage: uv run auditor.py <path_to_pdf_file>")
        sys.argv.append("sample.pdf") # Fallback to a default name for ease of testing
        
    try:
        report = run_auditor(sys.argv[1])
        print("\n✅ AUDIT COMPLETE. PARSED OUTPUT:")
        print(report.model_dump_json(indent=2))
    except Exception as e:
        print(f"\n❌ Execution Failed: {str(e)}")

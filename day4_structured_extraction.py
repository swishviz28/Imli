import os
import json

from dotenv import load_dotenv
from openai import OpenAI
from pdf_reader import extract_text_from_pdf

# 1. Load API key and initialize client
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 2. Load PDF text
pdf_path = "sample.pdf"  # change if your file has a different name
full_text = extract_text_from_pdf(pdf_path)

# To stay safe on token limits, just send the first chunk for now
text_chunk = full_text[:12000]

# 3. Build the prompt for structured extraction
system_message = (
    "You are an expert U.S. immigration law assistant. "
    "Given a USCIS or AAO decision, you extract key case facts into a strict JSON object. "
    "You NEVER guess or infer information. You ONLY extract information explicitly stated in the text."
)

user_message = f"""
Read the following USCIS/AAO decision text and extract the key information into a JSON object.

Return ONLY valid JSON. Do not include any explanation or commentary, just the JSON.

IMPORTANT RULES (DO NOT BREAK THESE):
- NEVER guess, infer, approximate, assume, or fabricate any information.
- ONLY include values that are explicitly stated in the text.
- If a value is not explicitly stated, set to null (for dates/numbers) or "unknown" (for strings).
- If you are unsure, return null/unknown.
- If the field cannot be copied VERBATIM from the text, return null/unknown.

The JSON object MUST have exactly these fields:

- case_id: string (ONLY if the decision text explicitly contains a case number, AAO reference, or receipt number. If not explicitly present, set to "unknown". Do NOT infer or guess.)
- visa_type: string or null (examples: "O-1", "H-1B", "EB-2", "unknown")
- case_type: string (examples: "initial", "appeal", "motion", "unknown")
- beneficiary_role: string or null
- decision_outcome: string (one of: "approved", "denied", "dismissed", "sustained", "withdrawn", "remanded", "unknown")
- decision_date: string or null (ONLY if explicitly shown. Use ISO format "YYYY-MM-DD". Do NOT infer or guess ANY dates.)
- service_center: string or null (ONLY if explicitly shown. Do NOT infer, even if hints exist.)
- aao_docket_number: string or null (ONLY if explicitly present. Never guess.)
- regulatory_citations: array of strings (ONLY citations explicitly shown)
- issues: array of strings
- criteria_met: array of strings
- criteria_not_met: array of strings
- procedural_issues: array of strings
- key_evidence: array of strings
- risk_factors: array of strings
- notes: string

If a field is not explicitly stated in the text, set it to null or "unknown" as appropriate.

Decision text:
{text_chunk}
"""

# 4. Call the OpenAI API with JSON response formatting
response = client.chat.completions.create(
    model="gpt-4.1-mini",
    response_format={"type": "json_object"},
    messages=[
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ],
)

raw_content = response.choices[0].message.content

# 5. Parse the JSON and pretty-print it

# Extract case_id from the filename (fallback only)
case_id_from_filename = os.path.basename(pdf_path)

try:
    data = json.loads(raw_content)
except json.JSONDecodeError:
    print("❌ Failed to parse JSON. Raw model output:")
    print(raw_content)
    raise

# Only override case_id if model returned unknown/null
if not data.get("case_id") or data["case_id"] in [None, "", "unknown"]:
    data["case_id"] = case_id_from_filename

print("\n📦 Structured extraction:")
print(json.dumps(data, indent=2))

# 6. Save to a JSON file for future use
output_path = "day4_extracted_case.json"
with open(output_path, "w") as f:
    json.dump(data, f, indent=2)

print(f"\n✅ Saved structured data to {output_path}")

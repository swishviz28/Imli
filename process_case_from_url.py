import os
import json
import hashlib

from dotenv import load_dotenv
from openai import OpenAI

from uscis_fetcher import download_pdf_bytes
from pdf_reader import extract_text_from_pdf_bytes

# Load API key
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CASES_DIR = "cases"
os.makedirs(CASES_DIR, exist_ok=True)


def url_to_cache_key(url: str) -> str:
    """
    Create a short, safe cache key from the URL using a hash.
    """
    h = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return h[:16]  # 16 hex chars is plenty


def get_cached_case(url: str):
    """
    Return cached JSON data for this URL if it exists, else None.
    """
    key = url_to_cache_key(url)
    json_path = os.path.join(CASES_DIR, f"{key}.json")
    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            data = json.load(f)
        return data
    return None


def save_cached_case(url: str, data: dict):
    """
    Save structured JSON data for this URL so we don't re-fetch the PDF.
    """
    key = url_to_cache_key(url)
    json_path = os.path.join(CASES_DIR, f"{key}.json")
    with open(json_path, "w") as f:
        json.dump(data, f, indent=2)


def process_uscis_case(url: str) -> dict:
    """
    On-demand pipeline:
    - Check cache
    - If not cached, download PDF once, extract text, call OpenAI
    - Store only JSON locally (no PDF), so we don't re-hit the USCIS URL
    - Return the structured JSON data as a Python dict
    """

    # 1) Check cache first
    cached = get_cached_case(url)
    if cached is not None:
        print(f"📦 Using cached structured data for URL:\n{url}\n")
        return cached

    # 2) Not cached: fetch PDF once
    print(f"🔗 Fetching PDF from: {url}")
    pdf_bytes = download_pdf_bytes(url)

    # 3) Extract text in memory
    print("📄 Extracting text from PDF (in memory)...")
    full_text = extract_text_from_pdf_bytes(pdf_bytes)
    text_chunk = full_text[:12000]

    # 4) Build prompt (strict, no-hallucination rules)
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

    # 5) Call OpenAI
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ],
    )

    raw_content = response.choices[0].message.content

    # 6) Parse JSON
    try:
        data = json.loads(raw_content)
    except json.JSONDecodeError:
        print("❌ Failed to parse JSON. Raw model output:")
        print(raw_content)
        raise

    # 7) Save to cache and return
    save_cached_case(url, data)
    print(f"\n✅ Saved structured data to cache in '{CASES_DIR}'")
    return data


if __name__ == "__main__":
    # Example manual test; replace with a real URL if you want
    test_url = "https://www.uscis.gov/sites/default/files/err/B5%20-%20Members%20of%20the%20Professions%20holding%20Advanced%20Degrees%20or%20Aliens%20of%20Exceptional%20Ability/Decisions_Issued_in_2025/MAR122025_01B5203.pdf"
    result = process_uscis_case(test_url)
    print(json.dumps(result, indent=2))

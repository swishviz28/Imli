import os
from dotenv import load_dotenv
from openai import OpenAI
from pdf_reader import extract_text_from_pdf

# Load API key
load_dotenv()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load PDF
pdf_path = "sample.pdf"   # Change if needed
pdf_text = extract_text_from_pdf(pdf_path)

# Limit text (to avoid flooding the model)
pdf_text_chunk = pdf_text[:12000]  # ~12k chars for safety

prompt = f"""
You are an immigration law analyst.
Summarize the following USCIS or AAO document in a clear, structured way.
Focus on:
- the visa type
- the key eligibility points
- the main issue(s)
- the decision outcome if shown
- any risk factors or red flags

Document text:
{pdf_text_chunk}
"""

response = openai_client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[{"role": "user", "content": prompt}]
)

print("\n📄 Summary:")
print(response.choices[0].message.content)

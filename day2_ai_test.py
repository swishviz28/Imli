import os
from dotenv import load_dotenv
from openai import OpenAI
import anthropic

# Load .env file variables (your secret keys)
load_dotenv()

# Read API keys from environment variables
openai_key = os.getenv("OPENAI_API_KEY")
anthropic_key = os.getenv("ANTHROPIC_API_KEY")

# Initialize clients
openai_client = OpenAI(api_key=openai_key)
anthropic_client = anthropic.Anthropic(api_key=anthropic_key)

# Immigration law prompt for testing
prompt = "Explain the O-1 visa requirements in simple terms."

print("🔹 Testing OpenAI...")
openai_response = openai_client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[{"role": "user", "content": prompt}]
)
print("OpenAI:", openai_response.choices[0].message.content)

print("\n🔹 Testing Anthropic (Claude)...")
claude_response = anthropic_client.messages.create(
    model="claude-3-haiku-20240307",
    max_tokens=300,
    messages=[{"role": "user", "content": prompt}]
)
print("Anthropic:", claude_response.content[0].text)

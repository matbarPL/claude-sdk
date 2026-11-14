from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv(".env")
client = Anthropic()

msg = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=32,
    messages=[{"role": "user", "content": "Reply with: Direct API OK"}]
)
print(msg.content[0].text, "| stop_reason:", msg.stop_reason, "| usage:", msg.usage)

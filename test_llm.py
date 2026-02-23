import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

res = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role":"user","content":"테스트 성공이라고 한국어로 한 줄만 말해줘"}],
)

print(res.choices[0].message.content)

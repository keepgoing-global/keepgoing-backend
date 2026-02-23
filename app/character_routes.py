print("### LOADED character_routes.py ###")

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from openai import OpenAI
import os, json

router = APIRouter(prefix="/api/character", tags=["character"])


# =========================
# Request / Response Models
# =========================

class CharacterGenerateRequest(BaseModel):
    assistant_name: str
    character_description: str


class CharacterGenerateResponse(BaseModel):
    character_name: str
    description: str
    speech_style: str
    first_message: str
    image_prompt: str
    avatar_data_url: str


# =========================
# OpenAI Client
# =========================

def create_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")
    return OpenAI(api_key=api_key)


# =========================
# Generate Character
# =========================

@router.post("/generate", response_model=CharacterGenerateResponse)
def generate_character(payload: CharacterGenerateRequest):

    name = payload.assistant_name.strip()
    desc = payload.character_description.strip()

    if not name or not desc:
        raise HTTPException(status_code=400, detail="assistant_name / character_description required")

    client = create_client()

    # 🔥 컨셉 기반 말투 + 수행비서 유지
    system_prompt = f"""
너는 한국어 서비스 'KeepGoing'의 수행비서 캐릭터를 설계한다.

사용자가 입력한 캐릭터 설명은 "외형 + 분위기 컨셉"이다.
그 컨셉을 바탕으로 말투, 성격, 코칭 스타일도 함께 도출한다.

규칙:
- 캐릭터 컨셉을 말투에 반영한다.
- 하지만 항상 "사용자의 성공을 돕는 수행비서" 역할을 유지한다.
- 동물이라도 짖거나 의성어를 쓰지 않는다.
- 유치한 말투 금지.
- 존댓말 또는 부드러운 반말 중 하나로 일관성 있게 유지.

입력:
- 비서 이름: {name}
- 캐릭터 컨셉: {desc}

반드시 JSON만 출력한다. 다른 텍스트 금지.

포함해야 할 키:
- character_name (string)
- description (외형 + 성격 + 분위기 2~4문장)
- speech_style (한 줄 말투 가이드)
- first_message (첫 인사)
- image_prompt (이미지 생성용 프롬프트)

first_message의 마지막 문장은 반드시:
"나는 너의 성공을 도와줄 {name}이야. 나는 너를 뭐라고 부르면 돼?"
로 끝나야 한다.
""".strip()

    # 1️⃣ LLM으로 캐릭터 텍스트 생성
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.7,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "JSON으로만 출력해."},
        ],
        response_format={"type": "json_object"},
    )

    obj = json.loads(res.choices[0].message.content)

    # 2️⃣ 이미지 생성
    img = client.images.generate(
    model="gpt-image-1",
    prompt=obj["image_prompt"],
    size="auto" \
    "",
)

    b64 = img.data[0].b64_json
    avatar_data_url = f"data:image/png;base64,{b64}"

    return {
        "character_name": obj.get("character_name", name),
        "description": obj["description"],
        "speech_style": obj["speech_style"],
        "first_message": obj["first_message"],
        "image_prompt": obj["image_prompt"],
        "avatar_data_url": avatar_data_url,
    }

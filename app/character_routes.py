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
# Korean particle helper
# =========================

def _name_with_yah(name: str) -> str:
    if not name:
        return "너야"
    ch = name[-1]
    code = ord(ch) - 0xAC00
    if 0 <= code <= 11171:
        jong = code % 28
        return f"{name}이야" if jong != 0 else f"{name}야"
    return f"{name}야"


# =========================
# Generate Character
# =========================

@router.post("/generate", response_model=CharacterGenerateResponse)
def generate_character(payload: CharacterGenerateRequest):

    name = (payload.assistant_name or "").strip()
    desc = (payload.character_description or "").strip()

    if not name or not desc:
        raise HTTPException(status_code=400, detail="assistant_name / character_description required")

    client = create_client()

    # =========================
    # 1️⃣ LLM: 캐릭터 설명/말투/이미지 컨셉 생성
    # =========================

    system_prompt = f"""
너는 한국어 서비스 'KeepGoing'의 수행비서 캐릭터를 설계한다.

사용자가 입력한 캐릭터 설명은 "외형 + 분위기 컨셉"이다.
그 컨셉을 바탕으로 성격, 말투 가이드, 이미지 컨셉을 만든다.

규칙:
- 수행비서/코치 역할 유지
- 유치한 말투 금지
- 의성어 금지
- 존댓말 또는 부드러운 반말 중 하나 유지
- 이미지에는 배경 요소 금지 (캐릭터만)

입력:
- 비서 이름: {name}
- 캐릭터 컨셉: {desc}

반드시 JSON만 출력한다.

포함해야 할 키:
- character_name (반드시 "{name}")
- description (외형 + 성격 2~4문장)
- speech_style (한 줄 말투 가이드)
- image_prompt (컨셉 설명용 텍스트)
""".strip()

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

    # =========================
    # 2️⃣ 이미지 생성 (2D 플랫 앱 아이콘 스타일 강제)
    # =========================

    base_style = """
Flat 2D vector illustration, clean mobile app avatar style,
simple shapes, soft pastel colors, minimal shading,
single character only, centered, no background,
no scenery, no text, no logo,
transparent background, isolated character,
modern UI icon style, friendly expression
""".strip()

    final_image_prompt = f"{base_style}. Character concept: {desc}"

    img = client.images.generate(
        model="gpt-image-1",
        prompt=final_image_prompt,
        size="auto",
    )

    b64 = img.data[0].b64_json
    avatar_data_url = f"data:image/png;base64,{b64}"

    # =========================
    # 3️⃣ first_message 서버 강제 고정
    # =========================

    first_message = f"너의 성공을 도와줄 {_name_with_yah(name)}.\n\n너를 뭐라고 부를까?"

    return {
        "character_name": obj.get("character_name", name),
        "description": obj["description"],
        "speech_style": obj["speech_style"],
        "first_message": first_message,
        "image_prompt": final_image_prompt,
        "avatar_data_url": avatar_data_url,
    }

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
    """
    받침 있으면 '이야', 없으면 '야'
    ex) 민찬 -> 민찬이야 / 몽이 -> 몽이야
    """
    if not name:
        return "너야"
    ch = name[-1]
    code = ord(ch) - 0xAC00
    if 0 <= code <= 11171:
        jong = code % 28
        return f"{name}이야" if jong != 0 else f"{name}야"
    # 한글이 아니면 기본 '야'
    return f"{name}야"


@router.post("/generate", response_model=CharacterGenerateResponse)
def generate_character(payload: CharacterGenerateRequest):
    name = (payload.assistant_name or "").strip()
    desc = (payload.character_description or "").strip()

    if not name or not desc:
        raise HTTPException(status_code=400, detail="assistant_name / character_description required")

    client = create_client()

    # ✅ LLM은 캐릭터 설명/말투/이미지프롬프트만 만들게 하고
    # ✅ first_message는 서버에서 강제 생성(중복/어색한 조사 방지)
    system_prompt = f"""
너는 한국어 서비스 'KeepGoing'의 수행비서 캐릭터를 설계한다.

사용자가 입력한 캐릭터 설명은 "외형 + 분위기 컨셉"이다.
그 컨셉을 바탕으로 성격, 코칭 스타일(말투 가이드), 이미지 생성 프롬프트를 만든다.

규칙:
- 캐릭터 컨셉을 말투/성격에 반영하되, 수행비서/코치 역할은 유지한다.
- 동물 컨셉이어도 의성어(멍멍/야옹) 금지.
- 유치한 말투 금지.
- 존댓말 또는 부드러운 반말 중 하나로 일관성 있게 유지.

입력:
- 비서 이름: {name}
- 캐릭터 컨셉: {desc}

반드시 JSON만 출력한다. 다른 텍스트 금지.

포함해야 할 키:
- character_name (string) : 반드시 "{name}"
- description (외형 + 성격 + 분위기 2~4문장)
- speech_style (한 줄 말투 가이드)
- image_prompt (이미지 생성용 프롬프트: 흰 배경, 전신, 3D 귀여운 스타일, 앱 아바타 느낌, 컨셉 강반영)
""".strip()

    # 1) 텍스트 생성 (JSON)
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

    # 2) 이미지 생성
    img = client.images.generate(
        model="gpt-image-1",
        prompt=obj["image_prompt"],
        size="auto",
    )
    b64 = img.data[0].b64_json
    avatar_data_url = f"data:image/png;base64,{b64}"

    # ✅ first_message는 여기서 “딱 2문장 + 문단 띄움”으로 고정
    first_message = f"너의 성공을 도와줄 {_name_with_yah(name)}.\n\n너를 뭐라고 부를까?"


    return {
        "character_name": obj.get("character_name", name),
        "description": obj["description"],
        "speech_style": obj["speech_style"],
        "first_message": first_message,
        "image_prompt": obj["image_prompt"],
        "avatar_data_url": avatar_data_url,
    }

print("### LOADED character_routes.py ###")
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from openai import OpenAI
import os, json

router = APIRouter(prefix="/api/character", tags=["character"])


class CharacterGenerateRequest(BaseModel):
    assistant_name: str
    character_description: str


class CharacterGenerateResponse(BaseModel):
    character_name: str
    description: str
    first_message: str
    image_prompt: str
    avatar_data_url: str


def create_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")
    return OpenAI(api_key=api_key)


@router.post("/generate", response_model=CharacterGenerateResponse)
def generate_character(payload: CharacterGenerateRequest):

    name = payload.assistant_name.strip()
    desc = payload.character_description.strip()

    if not name or not desc:
        raise HTTPException(status_code=400, detail="assistant_name / character_description required")

    client = create_client()

    system_prompt = f"""
너는 한국어 서비스 'KeepGoing'의 수행비서 캐릭터를 설계한다.
반드시 JSON만 출력한다. 다른 텍스트 금지.

요청:
- 비서 이름: {name}
- 캐릭터 설명: {desc}

아래 키를 반드시 포함:
- character_name
- description
- first_message
- image_prompt

first_message의 마지막 문장은 반드시:
"나는 너의 성공을 도와줄 {name}이야. 나는 너를 뭐라고 부르면 돼?"
로 끝나야 한다.
""".strip()

    # 1️⃣ LLM으로 캐릭터 정보 생성
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
        size="512x512",
    )

    b64 = img.data[0].b64_json
    avatar_data_url = f"data:image/png;base64,{b64}"

    return {
        "character_name": obj.get("character_name", name),
        "description": obj["description"],
        "first_message": obj["first_message"],
        "image_prompt": obj["image_prompt"],
        "avatar_data_url": avatar_data_url,
    }

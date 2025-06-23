from fastapi import FastAPI, Query
from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Union, Literal
import random

app = FastAPI()


# Модели для кнопок
class Button(BaseModel):
    text: str
    url: HttpUrl


# NS и OS
class AdBase(BaseModel):
    type: Literal["NS", "OS"]
    channels: Dict[str, HttpUrl]


# H
class AdH(BaseModel):
    type: Literal["H"]
    text: str
    media: List[HttpUrl]
    buttons: List[Button]


# Унифицированная модель
Ad = Union[AdBase, AdH]

H = [
    {
        "type": "H",
        "text": "🎉 Добро пожаловать в IUDA BOT!",
        "media_type": "photo",  # Может быть фото, видео, документ, гиф, альбом
        "media": ["https://ibb.co/HfZWZxF9", "https://ibb.co/HfZWZxF9"],
        "buttons": [{"text": "🔓 Перейти", "url": "https://example.com/bonus"}],
    }
]

OS_NS = [
    {
        "type": "NS",
        "channels": {
            "IUDA LAB": "https://t.me/iudalab",
            "Crypto Chat": "https://t.me/cryptochat",
        },
    },
    {"type": "OS", "channels": {"AI News": "https://t.me/ainews"}},
]


@app.get("/channels", response_model=List[Ad])
async def fetch_channels(
    user_id: int = Query(..., description="ID пользователя"),
) -> List[Ad]:
    return random.choice([H, OS_NS])


# Проверка подписки
class SubscriptionRequest(BaseModel):
    user_id: int
    channel_url: HttpUrl


@app.post("/is_subscribed")
async def is_subscribed(data: SubscriptionRequest):
    """
    Мокаем: на IUDA LAB подписан только если user_id чётный.
    На все остальные всегда нет.
    """
    if data.channel_url == "https://t.me/iudalab":
        result = data.user_id % 2 == 0
    else:
        result = False
    return {"subscribed": result}

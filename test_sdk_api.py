from fastapi import FastAPI, Header, Request
from fastapi.responses import JSONResponse
import itertools

app = FastAPI()

X_SDK_KEY = "test_sdk_key"
rotation = itertools.cycle(["H", "NS", "OS"])  # Ротация форматов


@app.post("/bot_events")
async def bot_events(request: Request, x_sdk_key: str = Header(..., alias="X-Sdk-Key")):
    if x_sdk_key != X_SDK_KEY:
        return JSONResponse(status_code=403, content={"detail": "Invalid SDK key"})
    data = await request.json()
    required = {
        "telegram_user_id",
        "is_premium",
        "full_user_data",
        "event_type",
        "event_name",
        "event_data",
    }
    if not required.issubset(data):
        return JSONResponse(status_code=400, content={"detail": "Missing fields"})
    return JSONResponse(status_code=201, content={"result": "ok"})


@app.post("/bot_serve")
async def bot_serve(request: Request, x_sdk_key: str = Header(..., alias="X-Sdk-Key")):
    if x_sdk_key != X_SDK_KEY:
        return JSONResponse(status_code=403, content={"detail": "Invalid SDK key"})
    data = await request.json()
    required = {"telegram_user_id", "is_premium", "full_user_data"}
    if not required.issubset(data):
        return JSONResponse(status_code=400, content={"detail": "Missing fields"})

    ad_type = next(rotation)

    if ad_type == "H":
        ads = [
            {
                "order_id": "1",
                "id": "101",
                "project_id": "201",
                "format": "H",
                "quest_link": "https://example.com/quest",
                "popup_link": "https://example.com/popup",
                "tg_text": "🔥 Супер акция! Не пропусти!",
                "tg_buttons": [{"text": "Перейти", "url": "https://example.com"}],
                "media": [{"type": "image", "url": "https://ibb.co/j953xdD5"}],
            }
        ]
    elif ad_type == "OS":
        ads = [
            {
                "order_id": "2",
                "id": "102",
                "project_id": "202",
                "format": "OS",
                "quest_link": "",
                "popup_link": "",
                "tg_text": "",
                "tg_buttons": [],
                "media": [],
                "channels": {
                    "Не обязательный Канал 1": "https://t.me/example_channel1",
                    "Не обязательный Канал 2": "https://t.me/example_channel2",
                },
            }
        ]
    else:
        ads = [
            {
                "order_id": "3",
                "id": "103",
                "project_id": "203",
                "format": "NS",
                "quest_link": "",
                "popup_link": "",
                "tg_text": "",
                "tg_buttons": [],
                "media": [],
                "channels": {"Обязательный Канал": "https://t.me/iudalab"},
            }
        ]

    return JSONResponse(status_code=200, content=ads)


@app.post("/bot_ad_goal")
async def bot_ad_goal(
    request: Request, x_sdk_key: str = Header(..., alias="X-Sdk-Key")
):
    if x_sdk_key != X_SDK_KEY:
        return JSONResponse(status_code=403, content={"detail": "Invalid SDK key"})
    data = await request.json()
    required = {"telegram_user_id", "full_user_data"}
    if not required.issubset(data):
        return JSONResponse(status_code=400, content={"detail": "Missing fields"})
    return JSONResponse(status_code=200, content={"result": "ad_goal_ok"})

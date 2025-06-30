from typing import Literal
import aiohttp

from .types import FullUserData, BotEventPayload


class LoggingService:
    def __init__(self, log_api_url: str, sdk_key: str):
        self.log_api_url = log_api_url
        self.sdk_key = sdk_key

    async def send_action_log(
        self,
        user_id: int,
        event_type: Literal["message", "callback_query", "custom_event"],
        full_user_data: FullUserData,
        details: dict[str, str],
    ) -> None:
        payload: BotEventPayload = {
            "telegram_user_id": str(user_id),
            "is_premium": int(full_user_data.get("is_premium") or False),
            "full_user_data": full_user_data,
            "event_type": "custom_event",  # согласно API
            "event_name": event_type,  # твой тип события
            "event_data": details,  # дополнительные данные
        }

        print(f"[USER LOG] {payload}")

        if self.log_api_url:
            headers = {"X-Sdk-Key": self.sdk_key, "Content-Type": "application/json"}
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.log_api_url, json=payload, headers=headers
                    ) as resp:
                        if resp.status != 201:
                            print(
                                f"Log API returned status {resp.status}: {await resp.text()}"
                            )
            except Exception as e:
                print(f"Log API error: {e}")

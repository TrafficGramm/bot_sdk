from typing import Dict

from datetime import datetime, timezone
import aiohttp

class LoggingService:
    def __init__(self, log_api_url: str):
        self.log_api_url = log_api_url

    async def send_action_log(self, user_id: int, event_type: str, details: dict[str, str]):
        log: Dict[str, str | int | dict[str, str]] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "event_type": event_type,
            "details": details
        }
        print(f"[USER LOG] {log}")
        if self.log_api_url:
            try:
                async with aiohttp.ClientSession() as session:
                    await session.post(self.log_api_url, json=log)
            except Exception as e:
                print(f"Log API error: {e}")

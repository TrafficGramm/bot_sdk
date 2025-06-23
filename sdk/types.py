from typing import TypedDict, Literal


class Button(TypedDict):
    text: str
    url: str


class AdH(TypedDict):
    type: Literal["H"]
    text: str
    media_type: str
    media: str | list[str]
    buttons: list[Button]


class AdOS(TypedDict):
    type: Literal["OS"]
    channels: dict[str, str]


class AdNS(TypedDict):
    type: Literal["NS"]
    channels: dict[str, str]


Ad = AdH | AdNS | AdOS


class FullUserData(TypedDict, total=False):
    id: int
    is_bot: bool
    is_premium: bool
    language_code: str
    first_name: str
    last_name: str | None
    username: str | None


class ServePayload(TypedDict):
    telegram_user_id: str
    is_premium: int
    full_user_data: FullUserData


class BotEventPayload(TypedDict):
    telegram_user_id: str
    is_premium: int
    full_user_data: FullUserData
    event_type: Literal["custom_event"]
    event_name: Literal["message", "callback_query", "custom_event"]
    event_data: dict[str, str]

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

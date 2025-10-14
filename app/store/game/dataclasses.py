from dataclasses import dataclass, field


@dataclass
class BotResponse:
    status: str
    chat_id: int
    message: str
    reply_markup: dict = field(default_factory=dict)
    data: dict = field(default_factory=dict)

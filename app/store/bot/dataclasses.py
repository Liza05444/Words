from dataclasses import dataclass, field


@dataclass
class MessageFrom:
    id: int
    first_name: str
    last_name: str
    username: str | None

    @staticmethod
    def load(res: dict) -> "MessageFrom":
        return MessageFrom(
            id=res["id"],
            first_name=res["first_name"],
            last_name=res.get("last_name", ""),
            username=res.get("username"),
        )


@dataclass
class Chat:
    id: int
    type: str
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    title: str | None = None

    @staticmethod
    def load(res: dict) -> "Chat":
        return Chat(
            id=res["id"],
            type=res["type"],
            first_name=res.get("first_name"),
            last_name=res.get("last_name"),
            username=res.get("username"),
            title=res.get("title"),
        )


@dataclass
class Message:
    from_: MessageFrom = field(metadata={"data_key": "from"})
    chat: Chat
    data: str | None = None

    @staticmethod
    def load(res: dict) -> "Message":
        if "callback_query" in res:
            return Message(
                from_=MessageFrom.load(res["callback_query"]["from"]), 
                chat=Chat.load(res["callback_query"]["message"]["chat"]), 
                data=res["callback_query"].get("data")
            )
        
        data = res.get("text")
        if "new_chat_participant" in res:
            data = (
                f"new {res["new_chat_participant"]["id"]} "
                f"{res["new_chat_participant"].get("first_name", "")} "
                f"{res["new_chat_participant"].get("last_name", "")}"
            )
        elif "left_chat_participant" in res:
            data = f"old {res["left_chat_participant"]["id"]}"
        
        return Message(
            from_=MessageFrom.load(res["from"]), 
            chat=Chat.load(res["chat"]), 
            data=data
        )


@dataclass
class UpdateObj:
    update_id: int
    status: str
    message: Message

    @staticmethod
    def load(res: dict) -> "UpdateObj":
        if "callback_query" in res:
            return UpdateObj(
                update_id=res["update_id"],
                status="callback",
                message=Message.load(res),
            )
        
        message = res.get("message", {})
        if message.get("text"):
            status = "message"
        elif "new_chat_participant" in message or "left_chat_participant" in message:
            status = "member"
        else:
            status = "message"
            
        return UpdateObj(
            update_id=res["update_id"],
            status=status,
            message=Message.load(message),
        )


@dataclass
class GetUpdatesResponse:
    ok: bool
    result: list[UpdateObj]

    @staticmethod
    def load(res: dict) -> "GetUpdatesResponse":
        updates = []
        
        if not res.get("ok") or "result" not in res:
            return GetUpdatesResponse(
                ok=res.get("ok", False),
                result=updates,
            )
        
        for upd in res["result"]:
            try:
                updates.append(UpdateObj.load(upd))
            except Exception:
                pass
                
        return GetUpdatesResponse(
            ok=res["ok"],
            result=updates,
        )


@dataclass
class SendMessageResponse:
    ok: bool
    result: Message | None

    @staticmethod
    def load(res: dict) -> "SendMessageResponse":
        if res.get("result") is None:
            return SendMessageResponse(ok=res["ok"], result=None)
        return SendMessageResponse(ok=res["ok"], result=Message.load(res["result"]))

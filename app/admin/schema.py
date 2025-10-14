from marshmallow import Schema, fields


class AdminInSchema(Schema):
    telegram_id = fields.Int(required=True, metadata={"description": "Telegram ID администратора"})


class UserSchema(Schema):
    id = fields.Int(required=True, metadata={"description": "ID пользователя"})
    telegram_id = fields.Int(required=True, metadata={"description": "Telegram ID пользователя"})
    name = fields.Str(required=True, metadata={"description": "Имя пользователя"})


class UserChatSchema(Schema):
    amount = fields.Int(required=True)
    users = fields.Nested(UserSchema, many=True)


class UserListSchema(Schema):
    amount = fields.Int(required=True)
    sessions = fields.Nested(UserChatSchema, many=True)


class SessionSchema(Schema):
    id = fields.Int(required=True, metadata={"description": "ID сессии"})
    chat_id = fields.Int(required=True, metadata={"description": "ID чата"})
    chat_name = fields.Str(required=True, metadata={"description": "Название чата"})
    state = fields.Int(required=True, metadata={"description": "Состояние игры"})
    member_amount = fields.Int(required=True, metadata={"description": "Количество участников"})
    current_user = fields.Int(required=True, metadata={"description": "Текущий игрок"})
    letter = fields.Str(required=True, metadata={"description": "Текущая буква"})
    delay = fields.Int(required=True, metadata={"description": "Задержка в секундах"})


class SessionListSchema(Schema):
    amount = fields.Int(required=True)
    sessions = fields.Nested(SessionSchema, many=True)

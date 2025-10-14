from marshmallow import Schema, fields


class UserInSchema(Schema):
    telegram_id = fields.Int(required=True)


class UserSchema(Schema):
    telegram_id = fields.Int(required=True)
    name = fields.Str(required=True)


class ChatSchema(Schema):
    chat_name = fields.Str(required=True)
    state = fields.Int(required=True)
    member_amount = fields.Int(required=True)
    current_user = fields.Int(required=True)
    letter = fields.Str(required=True)
    delay = fields.Int(required=True)


class ChatListSchema(Schema):
    sessions = fields.Nested(ChatSchema, many=True)


class UserResultSchema(Schema):
    name = fields.Str(required=True)
    count = fields.Int(required=True)


class ResultSchema(Schema):
    chat = fields.Str(required=True)
    result = fields.Nested(UserResultSchema, many=True)


class ResultListSchema(Schema):
    results = fields.Nested(ResultSchema, many=True)

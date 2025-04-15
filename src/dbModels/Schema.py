# schemas.py
from marshmallow import Schema, fields, validate

class UserSchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str(required=True)
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)
    role = fields.Str(validate=validate.OneOf(['admin', 'student', 'staff']))
    college_id = fields.Str(required=True)
    skill_level = fields.Int(validate=validate.Range(min=1, max=10))

class CollegeSchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str(required=True)
    location = fields.Str(required=True)
    contact_email = fields.Email(required=True)

class EventSchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str(required=True)
    description = fields.Str()
    start_date = fields.Str(required=True)
    end_date = fields.Str(required=True)
    status = fields.Str(validate=validate.OneOf(['planning', 'ongoing', 'completed', 'cancelled']))
    max_participants = fields.Int()
    registration_deadline = fields.Str()

class MatchSchema(Schema):
    id = fields.Str(dump_only=True)
    game_category_id = fields.Str(required=True)
    scheduled_time = fields.Str(required=True)
    status = fields.Str(validate=validate.OneOf(['scheduled', 'ongoing', 'completed', 'cancelled']))
    min_players = fields.Int()
    max_players = fields.Int()
    skill_level_range = fields.Int()

class TeamSchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str(required=True)
    skill_level = fields.Int(validate=validate.Range(min=1, max=10))
    captain_id = fields.Str()

class ParticipantSchema(Schema):
    user_id = fields.Str(required=True)
    match_id = fields.Str(required=True)
    participation_token = fields.Str(required=True)
    team_id = fields.Str()
    is_confirmed = fields.Bool()

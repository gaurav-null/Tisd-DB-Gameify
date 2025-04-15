# routes.py
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    jwt_required, create_access_token, get_jwt_identity
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from .models import (
    db, User, UserRole, College, RestrictedDay, Equipment, Event, 
    EventStatus, Sponsorship, Achievement, Match, MatchStatus,
    GameCategory, Participant, Team, Schedule, Venue, Certificate
)
from .schemas import (
    UserSchema, CollegeSchema, EventSchema, MatchSchema, 
    TeamSchema, ParticipantSchema
)
from marshmallow import ValidationError
import uuid

api = Blueprint('api', __name__)

# Initialize schemas
user_schema = UserSchema()
college_schema = CollegeSchema()
event_schema = EventSchema()
match_schema = MatchSchema()
team_schema = TeamSchema()
participant_schema = ParticipantSchema()

# Helper functions
def is_time_restricted(college_id, check_time):
    day_of_week = check_time.weekday()
    time_of_day = check_time.time()
    
    restricted_day = RestrictedDay.query.filter_by(
        college_id=college_id,
        day_of_week=day_of_week,
        is_restricted=True
    ).first()
    
    if not restricted_day:
        return False
    
    if restricted_day.restricted_start_time and restricted_day.restricted_end_time:
        start_time = restricted_day.restricted_start_time.time()
        end_time = restricted_day.restricted_end_time.time()
        return start_time <= time_of_day <= end_time
    
    return True

# Auth Routes
@api.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    try:
        user_data = user_schema.load(data)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    if User.query.filter_by(email=user_data['email']).first():
        return jsonify({"message": "Email already registered"}), 400
    
    hashed_password = generate_password_hash(user_data['password'])
    new_user = User(
        id=str(uuid.uuid4()),
        name=user_data['name'],
        email=user_data['email'],
        password_hash=hashed_password,
        role=user_data.get('role', UserRole.STUDENT),
        college_id=user_data['college_id']
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({"message": "User created successfully"}), 201

@api.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    user = User.query.filter_by(email=email).first()
    
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"message": "Invalid credentials"}), 401
    
    access_token = create_access_token(identity=user.id)
    return jsonify(access_token=access_token), 200

# User Routes
@api.route('/users/<user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    current_user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    
    if current_user_id != user_id and User.query.get(current_user_id).role != UserRole.ADMIN:
        return jsonify({"message": "Unauthorized"}), 403
    
    return user_schema.jsonify(user), 200

@api.route('/users/<user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    current_user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    
    if current_user_id != user_id and User.query.get(current_user_id).role != UserRole.ADMIN:
        return jsonify({"message": "Unauthorized"}), 403
    
    data = request.get_json()
    try:
        user_data = user_schema.load(data, partial=True)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    for key, value in user_data.items():
        if key == 'password':
            user.password_hash = generate_password_hash(value)
        else:
            setattr(user, key, value)
    
    db.session.commit()
    return jsonify({"message": "User updated successfully"}), 200

# College Routes (Admin only)
@api.route('/colleges', methods=['POST'])
@jwt_required()
def create_college():
    current_user = User.query.get(get_jwt_identity())
    if current_user.role != UserRole.ADMIN:
        return jsonify({"message": "Unauthorized"}), 403
    
    data = request.get_json()
    try:
        college_data = college_schema.load(data)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    new_college = College(
        id=str(uuid.uuid4()),
        name=college_data['name'],
        location=college_data['location'],
        contact_email=college_data['contact_email']
    )
    
    db.session.add(new_college)
    db.session.commit()
    
    return jsonify({"message": "College created successfully"}), 201

@api.route('/colleges/<college_id>/restricted-days', methods=['POST'])
@jwt_required()
def add_restricted_day(college_id):
    current_user = User.query.get(get_jwt_identity())
    if current_user.role != UserRole.ADMIN or current_user.college_id != college_id:
        return jsonify({"message": "Unauthorized"}), 403
    
    data = request.get_json()
    required_fields = ['day_of_week', 'is_restricted']
    if not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400
    
    restricted_day = RestrictedDay(
        id=str(uuid.uuid4()),
        college_id=college_id,
        day_of_week=data['day_of_week'],
        is_restricted=data['is_restricted'],
        restricted_start_time=data.get('restricted_start_time'),
        restricted_end_time=data.get('restricted_end_time')
    )
    
    db.session.add(restricted_day)
    db.session.commit()
    
    return jsonify({"message": "Restricted day added successfully"}), 201

# Event Routes
@api.route('/events', methods=['POST'])
@jwt_required()
def create_event():
    current_user = User.query.get(get_jwt_identity())
    data = request.get_json()
    
    try:
        event_data = event_schema.load(data)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    # Check if event times are during restricted hours
    start_time = datetime.fromisoformat(event_data['start_date'])
    end_time = datetime.fromisoformat(event_data['end_date'])
    
    if is_time_restricted(current_user.college_id, start_time) or is_time_restricted(current_user.college_id, end_time):
        return jsonify({"message": "Event cannot be scheduled during restricted college hours"}), 400
    
    new_event = Event(
        id=str(uuid.uuid4()),
        name=event_data['name'],
        organizer_id=current_user.id,
        description=event_data.get('description'),
        start_date=start_time,
        end_date=end_time,
        status=event_data.get('status', EventStatus.PLANNING),
        max_participants=event_data.get('max_participants'),
        registration_deadline=datetime.fromisoformat(event_data.get('registration_deadline')) if event_data.get('registration_deadline') else None
    )
    
    db.session.add(new_event)
    db.session.commit()
    
    return event_schema.jsonify(new_event), 201

# Match Routes
@api.route('/matches', methods=['POST'])
@jwt_required()
def create_match():
    current_user = User.query.get(get_jwt_identity())
    data = request.get_json()
    
    try:
        match_data = match_schema.load(data)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    # Check if match time is during restricted hours
    scheduled_time = datetime.fromisoformat(match_data['scheduled_time'])
    if is_time_restricted(current_user.college_id, scheduled_time):
        return jsonify({"message": "Match cannot be scheduled during restricted college hours"}), 400
    
    new_match = Match(
        id=str(uuid.uuid4()),
        game_category_id=match_data['game_category_id'],
        scheduled_time=scheduled_time,
        status=match_data.get('status', MatchStatus.SCHEDULED),
        min_players=match_data.get('min_players', 2),
        max_players=match_data.get('max_players', 10),
        skill_level_range=match_data.get('skill_level_range', 1)
    )
    
    db.session.add(new_match)
    db.session.commit()
    
    return match_schema.jsonify(new_match), 201

@api.route('/matches/<match_id>/register', methods=['POST'])
@jwt_required()
def register_for_match(match_id):
    current_user_id = get_jwt_identity()
    match = Match.query.get_or_404(match_id)
    
    # Check if match is already full
    participants_count = Participant.query.filter_by(match_id=match_id).count()
    if participants_count >= match.max_players:
        return jsonify({"message": "Match is already full"}), 400
    
    # Check if user is already registered
    existing_participation = Participant.query.filter_by(
        user_id=current_user_id,
        match_id=match_id
    ).first()
    
    if existing_participation:
        return jsonify({"message": "Already registered for this match"}), 400
    
    # Check skill level compatibility for matchmaking
    current_user = User.query.get(current_user_id)
    if match.skill_level_range > 0:
        # Get average skill level of current participants
        avg_skill = db.session.query(
            func.avg(User.skill_level)
        ).join(Participant).filter(
            Participant.match_id == match_id
        ).scalar() or current_user.skill_level
        
        if abs(current_user.skill_level - avg_skill) > match.skill_level_range:
            return jsonify({
                "message": "Your skill level doesn't match this game's requirements"
            }), 400
    
    new_participant = Participant(
        user_id=current_user_id,
        match_id=match_id,
        participation_token=str(uuid.uuid4()),
        is_confirmed=True
    )
    
    db.session.add(new_participant)
    db.session.commit()
    
    return participant_schema.jsonify(new_participant), 201

# Team Routes
@api.route('/teams', methods=['POST'])
@jwt_required()
def create_team():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    try:
        team_data = team_schema.load(data)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    new_team = Team(
        id=str(uuid.uuid4()),
        name=team_data['name'],
        skill_level=team_data.get('skill_level', 1),
        captain_id=current_user_id
    )
    
    db.session.add(new_team)
    db.session.commit()
    
    return team_schema.jsonify(new_team), 201

@api.route('/teams/<team_id>/join', methods=['POST'])
@jwt_required()
def join_team(team_id):
    current_user_id = get_jwt_identity()
    team = Team.query.get_or_404(team_id)
    
    # Check if user is already in the team
    existing_membership = Participant.query.filter_by(
        user_id=current_user_id,
        team_id=team_id
    ).first()
    
    if existing_membership:
        return jsonify({"message": "Already a member of this team"}), 400
    
    # In a real app, you'd probably have a team invitation system
    # For simplicity, we'll just add the user to the team
    
    # Find a match where the team is participating
    match = Match.query.join(Participant).filter(
        Participant.team_id == team_id
    ).first()
    
    if not match:
        return jsonify({"message": "Team is not registered for any matches"}), 400
    
    new_participant = Participant(
        user_id=current_user_id,
        match_id=match.id,
        team_id=team_id,
        participation_token=str(uuid.uuid4()),
        is_confirmed=True
    )
    
    db.session.add(new_participant)
    db.session.commit()
    
    return jsonify({"message": "Joined team successfully"}), 201

# Venue and Equipment Routes
@api.route('/venues', methods=['POST'])
@jwt_required()
def create_venue():
    current_user = User.query.get(get_jwt_identity())
    if current_user.role != UserRole.ADMIN:
        return jsonify({"message": "Unauthorized"}), 403
    
    data = request.get_json()
    required_fields = ['name', 'location', 'capacity']
    if not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400
    
    new_venue = Venue(
        id=str(uuid.uuid4()),
        name=data['name'],
        location=data['location'],
        capacity=data['capacity'],
        college_id=current_user.college_id
    )
    
    db.session.add(new_venue)
    db.session.commit()
    
    return jsonify({"message": "Venue created successfully"}), 201

@api.route('/equipment', methods=['POST'])
@jwt_required()
def add_equipment():
    current_user = User.query.get(get_jwt_identity())
    if current_user.role != UserRole.ADMIN:
        return jsonify({"message": "Unauthorized"}), 403
    
    data = request.get_json()
    required_fields = ['name', 'quantity']
    if not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400
    
    new_equipment = Equipment(
        id=str(uuid.uuid4()),
        name=data['name'],
        quantity=data['quantity'],
        condition=data.get('condition', 'good'),
        college_id=current_user.college_id
    )
    
    db.session.add(new_equipment)
    db.session.commit()
    
    return jsonify({"message": "Equipment added successfully"}), 201

# Schedule Routes
@api.route('/schedules', methods=['POST'])
@jwt_required()
def create_schedule():
    current_user = User.query.get(get_jwt_identity())
    if current_user.role != UserRole.ADMIN:
        return jsonify({"message": "Unauthorized"}), 403
    
    data = request.get_json()
    required_fields = ['match_id', 'venue_id', 'start_time', 'end_time']
    if not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400
    
    # Check venue availability
    venue = Venue.query.get(data['venue_id'])
    if not venue or not venue.is_available:
        return jsonify({"message": "Venue not available"}), 400
    
    # Check for scheduling conflicts
    start_time = datetime.fromisoformat(data['start_time'])
    end_time = datetime.fromisoformat(data['end_time'])
    
    conflicting_schedules = Schedule.query.filter(
        Schedule.venue_id == data['venue_id'],
        Schedule.start_time < end_time,
        Schedule.end_time > start_time
    ).count()
    
    if conflicting_schedules > 0:
        return jsonify({"message": "Venue already booked for this time"}), 400
    
    new_schedule = Schedule(
        id=str(uuid.uuid4()),
        match_id=data['match_id'],
        venue_id=data['venue_id'],
        start_time=start_time,
        end_time=end_time,
        equipment_needed=data.get('equipment_needed')
    )
    
    db.session.add(new_schedule)
    db.session.commit()
    
    return jsonify({"message": "Schedule created successfully"}), 201

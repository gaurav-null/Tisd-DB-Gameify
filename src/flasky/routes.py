# routes.py
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from src.dbModels.models import (
    User,
    UserRole,
    College,
    RestrictedDay,
    Equipment,
    Event,
    EventStatus,
    Sponsorship,
    Achievement,
    Match,
    MatchStatus,
    GameCategory,
    Participant,
    Team,
    Schedule,
    Venue,
    Certificate,
)
from marshmallow import ValidationError
import uuid
from src.dbModels import dbSession
session = dbSession()

api = Blueprint("api", __name__)

# Helper functions
def is_time_restricted(college_id, check_time):
    day_of_week = check_time.weekday()
    time_of_day = check_time.time()

    restricted_day = session.query(RestrictedDay).filter_by(
        college_id=college_id, day_of_week=day_of_week, is_restricted=True
    ).first()

    if not restricted_day:
        return False

    if restricted_day.restricted_start_time and restricted_day.restricted_end_time:
        start_time = restricted_day.restricted_start_time.time()
        end_time = restricted_day.restricted_end_time.time()
        return start_time <= time_of_day <= end_time

    return True

# Auth Routes
@api.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    required_fields = ["name", "email", "password", "college_id"]
    if not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400

    if session.query(User).filter_by(email=data["email"]).first():
        return jsonify({"message": "Email already registered"}), 400

    hashed_password = generate_password_hash(data["password"])
    new_user = User(
        id=str(uuid.uuid4()),
        name=data["name"],
        email=data["email"],
        password_hash=hashed_password,
        role=data.get("role", UserRole.STUDENT),
        college_id=data["college_id"],
    )

    session.add(new_user)
    session.commit()

    return jsonify({"message": "User created successfully"}), 201


@api.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    user = session.query(User).filter_by(email=email).first()

    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"message": "Invalid credentials"}), 401

    access_token = create_access_token(identity=user.id)
    return jsonify(access_token=access_token), 200


# User Routes
@api.route("/users/<user_id>", methods=["GET"])
@jwt_required()
def get_user(user_id):
    current_user_id = get_jwt_identity()
    user = session.query(User).get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    if (current_user_id != user_id and 
        session.query(User).get(current_user_id).role != UserRole.ADMIN):
        return jsonify({"message": "Unauthorized"}), 403

    return jsonify({
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role.value,
        "college_id": user.college_id,
        "skill_level": user.skill_level,
        "is_active": user.is_active
    }), 200


@api.route("/users/<user_id>", methods=["PUT"])
@jwt_required()
def update_user(user_id):
    current_user_id = get_jwt_identity()
    user = session.query(User).get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    if (current_user_id != user_id and 
        session.query(User).get(current_user_id).role != UserRole.ADMIN):
        return jsonify({"message": "Unauthorized"}), 403

    data = request.get_json()
    for key, value in data.items():
        if key == "password":
            user.password_hash = generate_password_hash(value)
        elif hasattr(user, key):
            setattr(user, key, value)

    session.commit()
    return jsonify({"message": "User updated successfully"}), 200


# College Routes (Admin only)
@api.route("/colleges", methods=["POST"])
@jwt_required()
def create_college():
    current_user = session.query(User).get(get_jwt_identity())
    if current_user.role != UserRole.ADMIN:
        return jsonify({"message": "Unauthorized"}), 403

    data = request.get_json()
    required_fields = ["name", "location", "contact_email"]
    if not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400

    new_college = College(
        id=str(uuid.uuid4()),
        name=data["name"],
        location=data["location"],
        contact_email=data["contact_email"],
    )

    session.add(new_college)
    session.commit()

    return jsonify({"message": "College created successfully"}), 201


@api.route("/colleges/<college_id>/restricted-days", methods=["POST"])
@jwt_required()
def add_restricted_day(college_id):
    current_user = session.query(User).get(get_jwt_identity())
    if current_user.role != UserRole.ADMIN or current_user.college_id != college_id:
        return jsonify({"message": "Unauthorized"}), 403

    data = request.get_json()
    required_fields = ["day_of_week", "is_restricted"]
    if not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400

    restricted_day = RestrictedDay(
        id=str(uuid.uuid4()),
        college_id=college_id,
        day_of_week=data["day_of_week"],
        is_restricted=data["is_restricted"],
        restricted_start_time=data.get("restricted_start_time"),
        restricted_end_time=data.get("restricted_end_time"),
    )

    session.add(restricted_day)
    session.commit()

    return jsonify({"message": "Restricted day added successfully"}), 201


# Event Routes
@api.route("/events", methods=["POST"])
@jwt_required()
def create_event():
    current_user = session.query(User).get(get_jwt_identity())
    data = request.get_json()

    required_fields = ["name", "start_date", "end_date"]
    if not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400

    try:
        start_time = datetime.fromisoformat(data["start_date"])
        end_time = datetime.fromisoformat(data["end_date"])
    except ValueError:
        return jsonify({"message": "Invalid date format"}), 400

    if is_time_restricted(current_user.college_id, start_time) or is_time_restricted(
        current_user.college_id, end_time
    ):
        return (
            jsonify(
                {"message": "Event cannot be scheduled during restricted college hours"}
            ),
            400,
        )

    new_event = Event(
        id=str(uuid.uuid4()),
        name=data["name"],
        organizer_id=current_user.id,
        description=data.get("description"),
        start_date=start_time,
        end_date=end_time,
        status=data.get("status", EventStatus.PLANNING),
        max_participants=data.get("max_participants"),
        registration_deadline=(
            datetime.fromisoformat(data["registration_deadline"])
            if data.get("registration_deadline")
            else None
        ),
    )

    session.add(new_event)
    session.commit()

    return jsonify({
        "id": new_event.id,
        "name": new_event.name,
        "status": new_event.status.value,
        "start_date": new_event.start_date.isoformat(),
        "end_date": new_event.end_date.isoformat()
    }), 201


# Match Routes
@api.route("/matches", methods=["POST"])
@jwt_required()
def create_match():
    current_user = session.query(User).get(get_jwt_identity())
    data = request.get_json()

    required_fields = ["game_category_id", "scheduled_time"]
    if not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400

    try:
        scheduled_time = datetime.fromisoformat(data["scheduled_time"])
    except ValueError:
        return jsonify({"message": "Invalid date format"}), 400

    if is_time_restricted(current_user.college_id, scheduled_time):
        return (
            jsonify(
                {"message": "Match cannot be scheduled during restricted college hours"}
            ),
            400,
        )

    new_match = Match(
        id=str(uuid.uuid4()),
        game_category_id=data["game_category_id"],
        scheduled_time=scheduled_time,
        status=data.get("status", MatchStatus.SCHEDULED),
        min_players=data.get("min_players", 2),
        max_players=data.get("max_players", 10),
        skill_level_range=data.get("skill_level_range", 1),
    )

    session.add(new_match)
    session.commit()

    return jsonify({
        "id": new_match.id,
        "status": new_match.status.value,
        "scheduled_time": new_match.scheduled_time.isoformat()
    }), 201


@api.route("/matches/<match_id>/register", methods=["POST"])
@jwt_required()
def register_for_match(match_id):
    current_user_id = get_jwt_identity()
    match = session.query(Match).get(match_id)
    if not match:
        return jsonify({"message": "Match not found"}), 404

    # Check if match is already full
    participants_count = session.query(Participant).filter_by(match_id=match_id).count()
    if participants_count >= match.max_players:
        return jsonify({"message": "Match is already full"}), 400

    # Check if user is already registered
    existing_participation = session.query(Participant).filter_by(
        user_id=current_user_id, match_id=match_id
    ).first()

    if existing_participation:
        return jsonify({"message": "Already registered for this match"}), 400

    # Check skill level compatibility for matchmaking
    current_user = session.query(User).get(current_user_id)
    if match.skill_level_range > 0:
        # Get average skill level of current participants
        avg_skill = (
            session.query(func.avg(User.skill_level))
            .join(Participant)
            .filter(Participant.match_id == match_id)
            .scalar()
            or current_user.skill_level
        )

        if abs(current_user.skill_level - avg_skill) > match.skill_level_range:
            return (
                jsonify(
                    {
                        "message": "Your skill level doesn't match this game's requirements"
                    }
                ),
                400,
            )

    new_participant = Participant(
        user_id=current_user_id,
        match_id=match_id,
        participation_token=str(uuid.uuid4()),
        is_confirmed=True,
    )

    session.add(new_participant)
    session.commit()

    return jsonify({
        "user_id": new_participant.user_id,
        "match_id": new_participant.match_id,
        "is_confirmed": new_participant.is_confirmed
    }), 201


# Team Routes
@api.route("/teams", methods=["POST"])
@jwt_required()
def create_team():
    current_user_id = get_jwt_identity()
    data = request.get_json()

    required_fields = ["name"]
    if not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400

    new_team = Team(
        id=str(uuid.uuid4()),
        name=data["name"],
        skill_level=data.get("skill_level", 1),
        captain_id=current_user_id,
    )

    session.add(new_team)
    session.commit()

    return jsonify({
        "id": new_team.id,
        "name": new_team.name,
        "skill_level": new_team.skill_level
    }), 201


@api.route("/teams/<team_id>/join", methods=["POST"])
@jwt_required()
def join_team(team_id):
    current_user_id = get_jwt_identity()
    team = session.query(Team).get(team_id)
    if not team:
        return jsonify({"message": "Team not found"}), 404

    # Check if user is already in the team
    existing_membership = session.query(Participant).filter_by(
        user_id=current_user_id, team_id=team_id
    ).first()

    if existing_membership:
        return jsonify({"message": "Already a member of this team"}), 400

    # Find a match where the team is participating
    match = session.query(Match).join(Participant).filter(Participant.team_id == team_id).first()

    if not match:
        return jsonify({"message": "Team is not registered for any matches"}), 400

    new_participant = Participant(
        user_id=current_user_id,
        match_id=match.id,
        team_id=team_id,
        participation_token=str(uuid.uuid4()),
        is_confirmed=True,
    )

    session.add(new_participant)
    session.commit()

    return jsonify({"message": "Joined team successfully"}), 201


# Venue and Equipment Routes
@api.route("/venues", methods=["POST"])
@jwt_required()
def create_venue():
    current_user = session.query(User).get(get_jwt_identity())
    if current_user.role != UserRole.ADMIN:
        return jsonify({"message": "Unauthorized"}), 403

    data = request.get_json()
    required_fields = ["name", "location", "capacity"]
    if not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400

    new_venue = Venue(
        id=str(uuid.uuid4()),
        name=data["name"],
        location=data["location"],
        capacity=data["capacity"],
        college_id=current_user.college_id,
    )

    session.add(new_venue)
    session.commit()

    return jsonify({"message": "Venue created successfully"}), 201


@api.route("/equipment", methods=["POST"])
@jwt_required()
def add_equipment():
    current_user = session.query(User).get(get_jwt_identity())
    if current_user.role != UserRole.ADMIN:
        return jsonify({"message": "Unauthorized"}), 403

    data = request.get_json()
    required_fields = ["name", "quantity"]
    if not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400

    new_equipment = Equipment(
        id=str(uuid.uuid4()),
        name=data["name"],
        quantity=data["quantity"],
        condition=data.get("condition", "good"),
        college_id=current_user.college_id,
    )

    session.add(new_equipment)
    session.commit()

    return jsonify({"message": "Equipment added successfully"}), 201


# Schedule Routes
@api.route("/schedules", methods=["POST"])
@jwt_required()
def create_schedule():
    current_user = session.query(User).get(get_jwt_identity())
    if current_user.role != UserRole.ADMIN:
        return jsonify({"message": "Unauthorized"}), 403

    data = request.get_json()
    required_fields = ["match_id", "venue_id", "start_time", "end_time"]
    if not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400

    # Check venue availability
    venue = session.query(Venue).get(data["venue_id"])
    if not venue or not venue.is_available:
        return jsonify({"message": "Venue not available"}), 400

    # Check for scheduling conflicts
    try:
        start_time = datetime.fromisoformat(data["start_time"])
        end_time = datetime.fromisoformat(data["end_time"])
    except ValueError:
        return jsonify({"message": "Invalid date format"}), 400

    conflicting_schedules = session.query(Schedule).filter(
        Schedule.venue_id == data["venue_id"],
        Schedule.start_time < end_time,
        Schedule.end_time > start_time,
    ).count()

    if conflicting_schedules > 0:
        return jsonify({"message": "Venue already booked for this time"}), 400

    new_schedule = Schedule(
        id=str(uuid.uuid4()),
        match_id=data["match_id"],
        venue_id=data["venue_id"],
        start_time=start_time,
        end_time=end_time,
        equipment_needed=data.get("equipment_needed"),
    )

    session.add(new_schedule)
    session.commit()

    return jsonify({"message": "Schedule created successfully"}), 201

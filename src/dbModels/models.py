# models.py
from sqlalchemy import (
    Column, Integer, String, ForeignKey, Boolean, DateTime, Text, DECIMAL,
    Enum, Date, func
)
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime, time
from enum import Enum as PyEnum
from .BaseModel import Base

class UserRole(str, PyEnum):
    ADMIN = 'admin'
    STUDENT = 'student'
    STAFF = 'staff'

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)  # For authentication
    role = Column(Enum(UserRole), nullable=False, default=UserRole.STUDENT)
    college_id = Column(String, ForeignKey("colleges.id"), nullable=False)
    skill_level = Column(Integer, default=1)  # For matchmaking
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    college = relationship("College", back_populates="users")
    achievements = relationship("Achievement", back_populates="user")
    participants = relationship("Participant", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, name={self.name}, email={self.email})>"


class College(Base):
    __tablename__ = "colleges"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    location = Column(String, nullable=False)
    contact_email = Column(String, nullable=False)

    users = relationship("User", back_populates="college")
    restricted_days = relationship("RestrictedDay", back_populates="college")
    equipment = relationship("Equipment", back_populates="college")

    def __repr__(self):
        return f"<College(id={self.id}, name={self.name})>"


class RestrictedDay(Base):
    __tablename__ = "restricted_days"

    id = Column(String, primary_key=True)
    college_id = Column(String, ForeignKey("colleges.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0-6 (Monday-Sunday)
    is_restricted = Column(Boolean, default=True)
    restricted_start_time = Column(DateTime)
    restricted_end_time = Column(DateTime)

    college = relationship("College", back_populates="restricted_days")

    def __repr__(self):
        return f"<RestrictedDay(id={self.id}, day={self.day_of_week})>"


class Equipment(Base):
    __tablename__ = "equipment"

    id = Column(String, primary_key=True)
    college_id = Column(String, ForeignKey("colleges.id"), nullable=False)
    name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    condition = Column(String)  # 'excellent', 'good', 'needs_replacement'

    college = relationship("College", back_populates="equipment")

    def __repr__(self):
        return f"<Equipment(id={self.id}, name={self.name})>"


class EventStatus(str, PyEnum):
    PLANNING = 'planning'
    ONGOING = 'ongoing'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'

class Event(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    organizer_id = Column(String, ForeignKey("users.id"), nullable=False)
    description = Column(Text)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    status = Column(Enum(EventStatus), nullable=False, default=EventStatus.PLANNING)
    max_participants = Column(Integer)
    registration_deadline = Column(DateTime)

    sponsorships = relationship("Sponsorship", back_populates="event")
    organizer = relationship("User")

    def __repr__(self):
        return f"<Event(id={self.id}, name={self.name}, status={self.status})>"


class Sponsorship(Base):
    __tablename__ = "sponsorships"

    id = Column(String, primary_key=True)
    event_id = Column(String, ForeignKey("events.id"), nullable=False)
    sponsor_name = Column(String, nullable=False)
    amount = Column(DECIMAL, nullable=False)
    contact_person = Column(String)
    contact_email = Column(String)

    event = relationship("Event", back_populates="sponsorships")

    def __repr__(self):
        return f"<Sponsorship(id={self.id}, sponsor_name={self.sponsor_name}, amount={self.amount})>"


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    date_achieved = Column(DateTime, default=datetime.utcnow)
    event_id = Column(String, ForeignKey("events.id"))

    user = relationship("User", back_populates="achievements")
    event = relationship("Event")

    def __repr__(self):
        return f"<Achievement(id={self.id}, user_id={self.user_id}, title={self.title})>"


class MatchStatus(str, PyEnum):
    SCHEDULED = 'scheduled'
    ONGOING = 'ongoing'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'

class Match(Base):
    __tablename__ = "matches"

    id = Column(String, primary_key=True)
    game_category_id = Column(String, ForeignKey("game_categories.id"), nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    status = Column(Enum(MatchStatus), nullable=False, default=MatchStatus.SCHEDULED)
    winner_id = Column(String, ForeignKey("teams.id"))
    min_players = Column(Integer, default=2)
    max_players = Column(Integer, default=10)
    skill_level_range = Column(Integer, default=1)  # Max skill difference allowed

    participants = relationship("Participant", back_populates="match")
    game_category = relationship("GameCategory", back_populates="matches")
    winner = relationship("Team", foreign_keys=[winner_id])
    schedules = relationship("Schedule", back_populates="match")

    def __repr__(self):
        return f"<Match(id={self.id}, status={self.status})>"


class GameCategory(Base):
    __tablename__ = "game_categories"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # 'individual' or 'team'
    description = Column(Text)
    rules = Column(Text)

    matches = relationship("Match", back_populates="game_category")

    def __repr__(self):
        return f"<GameCategory(id={self.id}, name={self.name}, type={self.type})>"


class Participant(Base):
    __tablename__ = "participants"

    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    match_id = Column(String, ForeignKey("matches.id"), primary_key=True)
    participation_token = Column(String, nullable=False)
    team_id = Column(String, ForeignKey("teams.id"))
    registration_date = Column(DateTime, default=datetime.utcnow)
    is_confirmed = Column(Boolean, default=False)

    user = relationship("User", back_populates="participants")
    match = relationship("Match", back_populates="participants")
    team = relationship("Team", back_populates="participants")
    certificates = relationship("Certificate", back_populates="participant")

    def __repr__(self):
        return f"<Participant(user_id={self.user_id}, match_id={self.match_id})>"


class Team(Base):
    __tablename__ = "teams"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    skill_level = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    captain_id = Column(String, ForeignKey("users.id"))

    participants = relationship("Participant", back_populates="team")
    captain = relationship("User")

    def __repr__(self):
        return f"<Team(id={self.id}, name={self.name}, skill_level={self.skill_level})>"


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(String, primary_key=True)
    match_id = Column(String, ForeignKey("matches.id"), nullable=False)
    venue_id = Column(String, ForeignKey("venues.id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    equipment_needed = Column(Text)  # JSON string of required equipment

    match = relationship("Match", back_populates="schedules")
    venue = relationship("Venue", back_populates="schedules")

    def __repr__(self):
        return f"<Schedule(id={self.id}, match_id={self.match_id})>"


class Venue(Base):
    __tablename__ = "venues"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    location = Column(String, nullable=False)
    capacity = Column(Integer, nullable=False)
    college_id = Column(String, ForeignKey("colleges.id"), nullable=False)
    is_available = Column(Boolean, default=True)

    schedules = relationship("Schedule", back_populates="venue")
    college = relationship("College")

    def __repr__(self):
        return f"<Venue(id={self.id}, name={self.name}, location={self.location})>"


class CertificateType(str, PyEnum):
    PARTICIPATION = 'participation'
    WINNER = 'winner'
    ACHIEVEMENT = 'achievement'

class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(String, primary_key=True)
    participant_id = Column(String, ForeignKey("participants.user_id"), nullable=False)
    match_id = Column(String, ForeignKey("matches.id"))
    type = Column(Enum(CertificateType), nullable=False)
    date_issued = Column(DateTime, default=datetime.utcnow)
    download_url = Column(String)

    participant = relationship("Participant", back_populates="certificates")
    match = relationship("Match")

    def __repr__(self):
        return f"<Certificate(id={self.id}, participant_id={self.participant_id})>"

from sqlalchemy import (
    Column, Integer, String, ForeignKey, Boolean, DateTime, Text, DECIMAL
)
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    role = Column(String, nullable=False)
    college_id = Column(String, ForeignKey("colleges.id"), nullable=False)

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

    users = relationship("User", back_populates="college")

    def __repr__(self):
        return f"<College(id={self.id}, name={self.name})>"


class Event(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    organizer_id = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    status = Column(String, nullable=False)

    sponsorships = relationship("Sponsorship", back_populates="event")

    def __repr__(self):
        return f"<Event(id={self.id}, name={self.name}, status={self.status})>"


class Sponsorship(Base):
    __tablename__ = "sponsorships"

    id = Column(String, primary_key=True)
    event_id = Column(String, ForeignKey("events.id"), nullable=False)
    sponsor_name = Column(String, nullable=False)
    amount = Column(DECIMAL, nullable=False)

    event = relationship("Event", back_populates="sponsorships")

    def __repr__(self):
        return f"<Sponsorship(id={self.id}, sponsor_name={self.sponsor_name}, amount={self.amount})>"


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    description = Column(Text, nullable=False)
    date_achieved = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="achievements")

    def __repr__(self):
        return f"<Achievement(id={self.id}, user_id={self.user_id}, description={self.description})>"


class Match(Base):
    __tablename__ = "matches"

    id = Column(String, primary_key=True)
    game_category_id = Column(String, ForeignKey("game_categories.id"), nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    status = Column(String, nullable=False)
    winner_id = Column(String, ForeignKey("teams.id"))

    participants = relationship("Participant", back_populates="match")
    game_category = relationship("GameCategory", back_populates="matches")
    winner = relationship("Team", foreign_keys=[winner_id])

    def __repr__(self):
        return f"<Match(id={self.id}, status={self.status})>"


class GameCategory(Base):
    __tablename__ = "game_categories"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)

    matches = relationship("Match", back_populates="game_category")

    def __repr__(self):
        return f"<GameCategory(id={self.id}, name={self.name}, type={self.type})>"


class Participant(Base):
    __tablename__ = "participants"

    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    match_id = Column(String, ForeignKey("matches.id"), primary_key=True)
    participation_token = Column(String, nullable=False)
    team_id = Column(String, ForeignKey("teams.id"))

    user = relationship("User", back_populates="participants")
    match = relationship("Match", back_populates="participants")
    team = relationship("Team", back_populates="participants")

    def __repr__(self):
        return f"<Participant(user_id={self.user_id}, match_id={self.match_id})>"


class Team(Base):
    __tablename__ = "teams"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    skill_level = Column(Integer, nullable=False)

    participants = relationship("Participant", back_populates="team")

    def __repr__(self):
        return f"<Team(id={self.id}, name={self.name}, skill_level={self.skill_level})>"


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(String, primary_key=True)
    match_id = Column(String, ForeignKey("matches.id"), nullable=False)
    venue_id = Column(String, ForeignKey("venues.id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)

    match = relationship("Match")
    venue = relationship("Venue")

    def __repr__(self):
        return f"<Schedule(id={self.id}, match_id={self.match_id})>"


class Venue(Base):
    __tablename__ = "venues"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    location = Column(String, nullable=False)
    capacity = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<Venue(id={self.id}, name={self.name}, location={self.location})>"


class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(String, primary_key=True)
    participant_id = Column(String, ForeignKey("participants.user_id"), nullable=False)
    type = Column(String, nullable=False)
    date_issued = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Certificate(id={self.id}, participant_id={self.participant_id})>"
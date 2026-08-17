from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class LostItem(Base):
    __tablename__ = "lost_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    category = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=False)
    color = Column(String, nullable=True)
    brand = Column(String, nullable=True)
    model = Column(String, nullable=True)
    location = Column(String, nullable=False, index=True)
    date_lost = Column(String, nullable=False) # YYYY-MM-DD
    distinctive_features = Column(JSON, nullable=True) # Extracted list of features
    extracted_tags = Column(JSON, nullable=True) # Full AI extracted structured JSON
    image_url = Column(String, nullable=True)
    status = Column(String, default="active") # "active", "matched", "returned"
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="lost_items")
    matches = relationship("Match", back_populates="lost_item", cascade="all, delete-orphan")


class FoundItem(Base):
    __tablename__ = "found_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    category = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=False)
    color = Column(String, nullable=True)
    brand = Column(String, nullable=True)
    model = Column(String, nullable=True)
    location = Column(String, nullable=False, index=True)
    date_found = Column(String, nullable=False) # YYYY-MM-DD
    distinctive_features = Column(JSON, nullable=True) # Extracted list of features
    extracted_tags = Column(JSON, nullable=True) # Full AI extracted structured JSON
    image_url = Column(String, nullable=True)
    status = Column(String, default="active") # "active", "matched", "returned"
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="found_items")
    matches = relationship("Match", back_populates="found_item", cascade="all, delete-orphan")


class ItemImage(Base):
    __tablename__ = "item_images"

    id = Column(Integer, primary_key=True, index=True)
    item_type = Column(String, nullable=False) # "lost" or "found"
    item_id = Column(Integer, nullable=False)
    file_path = Column(String, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    lost_item_id = Column(Integer, ForeignKey("lost_items.id"), nullable=False)
    found_item_id = Column(Integer, ForeignKey("found_items.id"), nullable=False)
    match_score = Column(Float, nullable=False) # 0.0 to 100.0
    factor_breakdown = Column(JSON, nullable=True) # Details of score breakdown
    confidence_level = Column(String, nullable=False) # "high", "medium", "low"
    reasons = Column(JSON, nullable=True) # list of human-readable match explanations
    status = Column(String, default="suggested") # "suggested", "verification_pending", "in_verification", "pending_admin", "approved", "rejected", "returned"
    admin_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    lost_item = relationship("LostItem", back_populates="matches")
    found_item = relationship("FoundItem", back_populates="matches")
    questions = relationship("VerificationQuestion", back_populates="match", cascade="all, delete-orphan")
    admin_actions = relationship("AdminAction", back_populates="match", cascade="all, delete-orphan")


class VerificationQuestion(Base):
    __tablename__ = "verification_questions"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String, default="general", nullable=True) # "brand", "color", "location", "feature", "date", "circumstances"
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    match = relationship("Match", back_populates="questions")
    answers = relationship("VerificationAnswer", back_populates="question", cascade="all, delete-orphan")

    @property
    def question(self):
        return self.question_text

    @question.setter
    def question(self, value):
        self.question_text = value


class VerificationAnswer(Base):
    __tablename__ = "verification_answers"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("verification_questions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    answer_text = Column(Text, nullable=False)
    evaluation_score = Column(Float, nullable=True) # AI evaluated score
    evaluation_feedback = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    question = relationship("VerificationQuestion", back_populates="answers")

    @property
    def answer(self):
        return self.answer_text

    @answer.setter
    def answer(self, value):
        self.answer_text = value

    @property
    def score(self):
        return self.evaluation_score

    @score.setter
    def score(self, value):
        self.evaluation_score = value

    @property
    def evaluation(self):
        return self.evaluation_feedback

    @evaluation.setter
    def evaluation(self, value):
        self.evaluation_feedback = value


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String, nullable=False) # "match_found", "verification_needed", "admin_update", "status_change"
    link = Column(String, nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="notifications")


class AdminAction(Base):
    __tablename__ = "admin_actions"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False) # "approved", "rejected", "requested_more_info"
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    match = relationship("Match", back_populates="admin_actions")

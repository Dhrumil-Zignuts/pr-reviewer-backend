from sqlalchemy import Column, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.models.base import Base


class UserSystemPrompt(Base):
    __tablename__ = "user_system_prompts"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    system_prompt = Column(Text, nullable=False)

    # Relationships
    user = relationship("User", backref="system_prompt_ref")

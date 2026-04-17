from sqlalchemy import Column, Integer, String, ForeignKey
from .base import Base

class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    action_type = Column(String(20), nullable=False)  
    
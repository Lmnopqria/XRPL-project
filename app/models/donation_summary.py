from sqlalchemy import Column, Integer, Float
from app.core.database import Base

class DonationSummary(Base):
    __tablename__ = "donation_summary"

    id = Column(Integer, primary_key=True)
    total = Column(Float, default=0.0, nullable=False)

    def __repr__(self):
        return f"<DonationSummary(id={self.id}, total={self.total})>" 
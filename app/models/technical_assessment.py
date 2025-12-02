from sqlalchemy import Column, ForeignKey, Integer, Enum as SQLEnum
from app.models.test import Test
from app.models.enums.scale import Scale

class TechnicalAssessment(Test):
    __tablename__ = "technical_assessments"
    
    id = Column(Integer, ForeignKey("tests.id"), primary_key=True)
    
    ball_control = Column(
        SQLEnum(Scale, name="scale_enum", create_constraint=False),
        nullable=True
    )
    short_pass = Column(
        SQLEnum(Scale, name="scale_enum", create_constraint=False),
        nullable=True
    )
    long_pass = Column(
        SQLEnum(Scale, name="scale_enum", create_constraint=False),
        nullable=True
    )
    shooting = Column(
        SQLEnum(Scale, name="scale_enum", create_constraint=False),
        nullable=True
    )
    dribbling = Column(
        SQLEnum(Scale, name="scale_enum", create_constraint=False),
        nullable=True
    )
    
    # Polimorfismo
    __mapper_args__ = {
        'polymorphic_identity': 'technical_assessment',
    }
    
    def __repr__(self):
        return f"<TechnicalAssessment(id={self.id}, athlete_id={self.athlete_id})>"
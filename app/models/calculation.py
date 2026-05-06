# File: app/models/calculation.py
# Purpose: SQLAlchemy models for calculations — single-table polymorphic inheritance.
#          Platform-independent GUID type works with PostgreSQL and SQLite.
import uuid
from datetime import datetime
from typing import List

from sqlalchemy import Column, DateTime, Float, ForeignKey, JSON, String, CHAR
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declared_attr, relationship
from sqlalchemy.types import TypeDecorator

from app.database import Base


class GUID(TypeDecorator):
    """UUID that uses native UUID on PostgreSQL, CHAR(36) on SQLite/others."""
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":  # pragma: no cover
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, uuid.UUID):  # pragma: no cover
            return str(uuid.UUID(str(value)))  # pragma: no cover
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, uuid.UUID):
            return uuid.UUID(str(value))
        return value


class AbstractCalculation:
    """Shared columns and logic for all calculation types."""

    @declared_attr
    def __tablename__(cls):
        return "calculations"

    @declared_attr
    def id(cls):
        return Column(GUID(), primary_key=True, default=uuid.uuid4, nullable=False)

    @declared_attr
    def user_id(cls):
        return Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    @declared_attr
    def type(cls):
        return Column(String(50), nullable=False, index=True)

    @declared_attr
    def inputs(cls):
        return Column(JSON, nullable=False)

    @declared_attr
    def result(cls):
        return Column(Float, nullable=True)

    @declared_attr
    def created_at(cls):
        return Column(DateTime, default=datetime.utcnow, nullable=False)

    @declared_attr
    def updated_at(cls):
        return Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    @declared_attr
    def user(cls):
        return relationship("User", back_populates="calculations")

    @classmethod
    def create(cls, calculation_type: str, user_id, inputs: List[float]) -> "Calculation":
        classes = {
            "addition": Addition, "subtraction": Subtraction,
            "multiplication": Multiplication, "division": Division,
            "modulo": Modulo, "power": Power,
        }
        klass = classes.get(calculation_type.lower())
        if not klass:
            raise ValueError(f"Unsupported calculation type: {calculation_type}")
        return klass(user_id=user_id, inputs=inputs)

    def get_result(self) -> float:
        raise NotImplementedError

    def __repr__(self):
        return f"<Calculation(type={self.type}, inputs={self.inputs})>"


class Calculation(Base, AbstractCalculation):
    __mapper_args__ = {"polymorphic_on": "type", "polymorphic_identity": "calculation"}


class Addition(Calculation):
    __mapper_args__ = {"polymorphic_identity": "addition"}
    def get_result(self) -> float:
        if not isinstance(self.inputs, list): raise ValueError("Inputs must be a list of numbers.")
        if len(self.inputs) < 2: raise ValueError("At least two numbers are required.")
        return sum(float(x) for x in self.inputs)


class Subtraction(Calculation):
    __mapper_args__ = {"polymorphic_identity": "subtraction"}
    def get_result(self) -> float:
        if not isinstance(self.inputs, list): raise ValueError("Inputs must be a list of numbers.")
        if len(self.inputs) < 2: raise ValueError("At least two numbers are required.")
        r = float(self.inputs[0])
        for v in self.inputs[1:]: r -= float(v)
        return r


class Multiplication(Calculation):
    __mapper_args__ = {"polymorphic_identity": "multiplication"}
    def get_result(self) -> float:
        if not isinstance(self.inputs, list): raise ValueError("Inputs must be a list of numbers.")
        if len(self.inputs) < 2: raise ValueError("At least two numbers are required.")
        r = 1.0
        for v in self.inputs: r *= float(v)
        return r


class Division(Calculation):
    __mapper_args__ = {"polymorphic_identity": "division"}
    def get_result(self) -> float:
        if not isinstance(self.inputs, list): raise ValueError("Inputs must be a list of numbers.")
        if len(self.inputs) < 2: raise ValueError("At least two numbers are required.")
        r = float(self.inputs[0])
        for v in self.inputs[1:]:
            if float(v) == 0: raise ValueError("Cannot divide by zero.")
            r /= float(v)
        return r


class Modulo(Calculation):
    __mapper_args__ = {"polymorphic_identity": "modulo"}
    def get_result(self) -> float:
        if not isinstance(self.inputs, list): raise ValueError("Inputs must be a list of numbers.")
        if len(self.inputs) < 2: raise ValueError("At least two numbers are required.")
        r = float(self.inputs[0])
        for v in self.inputs[1:]:
            if float(v) == 0: raise ValueError("Cannot modulo by zero.")
            r = r % float(v)
        return r


class Power(Calculation):
    __mapper_args__ = {"polymorphic_identity": "power"}
    def get_result(self) -> float:
        if not isinstance(self.inputs, list): raise ValueError("Inputs must be a list of numbers.")
        if len(self.inputs) < 2: raise ValueError("At least two numbers are required.")
        r = float(self.inputs[0])
        for v in self.inputs[1:]: r = r ** float(v)
        return r

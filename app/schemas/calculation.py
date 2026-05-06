# File: app/schemas/calculation.py
# Purpose: Pydantic schemas for creating, updating, and returning calculations.
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CalculationType(str, Enum):
    ADDITION       = "addition"
    SUBTRACTION    = "subtraction"
    MULTIPLICATION = "multiplication"
    DIVISION       = "division"
    MODULO         = "modulo"
    POWER          = "power"


class CalculationBase(BaseModel):
    type: CalculationType = Field(..., description="Operation type")
    inputs: List[float]   = Field(..., description="At least two numeric inputs")

    @field_validator("type", mode="before")
    @classmethod
    def normalize_type(cls, v):
        allowed = {e.value for e in CalculationType}
        if not isinstance(v, str) or v.lower() not in allowed:
            raise ValueError(f"Type must be one of: {', '.join(sorted(allowed))}")
        return v.lower()

    @field_validator("inputs", mode="before")
    @classmethod
    def coerce_inputs(cls, v):
        # Accept comma-separated string like "1,2,3" in addition to a list
        if isinstance(v, str):
            try:
                v = [float(x.strip()) for x in v.split(",") if x.strip()]
            except ValueError:
                raise ValueError("All inputs must be valid numbers separated by commas")
        if not isinstance(v, list):
            raise ValueError("Inputs must be a list of numbers")
        return v

    @model_validator(mode="after")
    def validate_inputs(self) -> "CalculationBase":
        if len(self.inputs) < 2:
            raise ValueError("At least two numbers are required")
        if self.type == CalculationType.DIVISION:
            if any(x == 0 for x in self.inputs[1:]):
                raise ValueError("Cannot divide by zero")
        if self.type == CalculationType.MODULO:
            if any(x == 0 for x in self.inputs[1:]):
                raise ValueError("Cannot modulo by zero")
        return self

    model_config = ConfigDict(from_attributes=True)


class CalculationCreate(CalculationBase):
    user_id: UUID


class CalculationUpdate(BaseModel):
    type:   Optional[CalculationType] = None
    inputs: Optional[List[float]]     = Field(None, description="Updated inputs (at least 2)")

    @field_validator("type", mode="before")
    @classmethod
    def normalize_type(cls, v):
        if v is None:
            return v
        allowed = {e.value for e in CalculationType}
        if not isinstance(v, str) or v.lower() not in allowed:
            raise ValueError(f"Type must be one of: {', '.join(sorted(allowed))}")
        return v.lower()

    @field_validator("inputs", mode="before")
    @classmethod
    def coerce_inputs(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            try:
                v = [float(x.strip()) for x in v.split(",") if x.strip()]
            except ValueError:
                raise ValueError("All inputs must be valid numbers")
        if not isinstance(v, list):
            raise ValueError("Inputs must be a list of numbers")
        return v

    @model_validator(mode="after")
    def validate_inputs(self) -> "CalculationUpdate":
        if self.inputs is not None and len(self.inputs) < 2:
            raise ValueError("At least two numbers are required")
        return self

    model_config = ConfigDict(from_attributes=True)


class CalculationResponse(CalculationBase):
    id:         UUID
    user_id:    UUID
    result:     float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CalculationStatsResponse(BaseModel):
    """Aggregated stats for the current user's calculation history."""
    total_count:    int
    by_type:        Dict[str, int]
    average_result: Optional[float]
    last_5:         List[CalculationResponse]

    model_config = ConfigDict(from_attributes=True)

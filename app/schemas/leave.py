from datetime import date, datetime

from pydantic import BaseModel, Field


class LeaveCreate(BaseModel):
    leave_type: str
    start_date: date
    end_date: date
    reason: str = Field(min_length=1, max_length=500)


class LeaveStatusUpdate(BaseModel):
    status: str
    rejection_reason: str | None = None


class LeaveResponse(BaseModel):
    id: int
    employee_id: int
    leave_type: str
    start_date: date
    end_date: date
    total_days: int
    reason: str
    status: str
    approved_by: int | None
    rejection_reason: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
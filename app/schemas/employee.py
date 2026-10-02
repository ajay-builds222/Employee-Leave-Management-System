from datetime import date
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field


class EmployeeCreate(BaseModel):
    employee_code: str
    name: str
    email: EmailStr
    phone: str = Field(pattern=r"^\d{10}$")
    department_id: int
    designation: str
    salary: Decimal = Field(gt=0)
    date_of_joining: date
    employment_type: str


class EmployeeUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = Field(default=None, pattern=r"^\d{10}$")
    department_id: int | None = None
    designation: str | None = None
    salary: Decimal | None = Field(default=None, gt=0)
    date_of_joining: date | None = None
    employment_type: str | None = None
    is_active: bool | None = None


class EmployeeResponse(BaseModel):
    id: int
    employee_code: str
    name: str
    email: EmailStr
    phone: str
    department_id: int
    designation: str
    salary: Decimal
    date_of_joining: date
    employment_type: str
    is_active: bool

    class Config:
        from_attributes = True
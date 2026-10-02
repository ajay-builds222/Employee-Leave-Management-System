from pydantic import BaseModel


class DepartmentCreate(BaseModel):
    department_name: str
    location: str


class DepartmentUpdate(BaseModel):
    department_name: str | None = None
    location: str | None = None
    is_active: bool | None = None


class DepartmentResponse(BaseModel):
    id: int
    department_name: str
    location: str
    is_active: bool

    class Config:
        from_attributes = True
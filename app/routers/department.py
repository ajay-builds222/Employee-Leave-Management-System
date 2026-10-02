from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.database import get_db
from app.models.department import Department
from app.schemas.department import (
    DepartmentCreate,
    DepartmentResponse,
    DepartmentUpdate,
)

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.post(
    "",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED
)
def create_department(
    data: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin", "HR"))
):
    existing = db.query(Department).filter(
        Department.department_name == data.department_name
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Department already exists"
        )

    department = Department(
        department_name=data.department_name,
        location=data.location
    )

    db.add(department)
    db.commit()
    db.refresh(department)

    return department


@router.get("", response_model=list[DepartmentResponse])
def get_departments(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin", "HR", "Employee"))
):
    return db.query(Department).filter(
        Department.is_active == True
    ).all()


@router.get("/{department_id}", response_model=DepartmentResponse)
def get_department(
    department_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin", "HR", "Employee"))
):
    department = db.query(Department).filter(
        Department.id == department_id,
        Department.is_active == True
    ).first()

    if not department:
        raise HTTPException(
            status_code=404,
            detail="Department not found"
        )

    return department


@router.put("/{department_id}", response_model=DepartmentResponse)
def update_department(
    department_id: int,
    data: DepartmentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin", "HR"))
):
    department = db.query(Department).filter(
        Department.id == department_id
    ).first()

    if not department:
        raise HTTPException(
            status_code=404,
            detail="Department not found"
        )

    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(department, key, value)

    db.commit()
    db.refresh(department)

    return department


@router.delete("/{department_id}")
def delete_department(
    department_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin"))
):
    department = db.query(Department).filter(
        Department.id == department_id
    ).first()

    if not department:
        raise HTTPException(
            status_code=404,
            detail="Department not found"
        )

    department.is_active = False

    db.commit()

    return {
        "message": "Department deactivated successfully"
    }
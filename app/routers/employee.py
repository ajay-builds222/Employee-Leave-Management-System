from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.database import get_db
from app.models.employee import Employee
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeResponse,
    EmployeeUpdate,
)

router = APIRouter(prefix="/employees", tags=["Employees"])


@router.post(
    "",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED
)
def create_employee(
    data: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin", "HR"))
):
    if data.date_of_joining > date.today():
        raise HTTPException(
            status_code=400,
            detail="Date of joining cannot be in the future"
        )

    if db.query(Employee).filter(
        Employee.employee_code == data.employee_code
    ).first():
        raise HTTPException(
            status_code=400,
            detail="Employee code already exists"
        )

    if db.query(Employee).filter(
        Employee.email == data.email
    ).first():
        raise HTTPException(
            status_code=400,
            detail="Employee email already exists"
        )

    employee = Employee(
        employee_code=data.employee_code,
        name=data.name,
        email=data.email,
        phone=data.phone,
        department_id=data.department_id,
        designation=data.designation,
        salary=data.salary,
        date_of_joining=data.date_of_joining,
        employment_type=data.employment_type,
        is_active=True
    )

    db.add(employee)
    db.commit()
    db.refresh(employee)

    return employee


@router.get("", response_model=list[EmployeeResponse])
def get_employees(
    page: int = 1,
    limit: int = 10,
    search: str | None = None,
    department_id: int | None = None,
    sort_by: str = "id",
    sort_order: str = "asc",
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin", "HR"))
):
    if page < 1:
        raise HTTPException(
            status_code=400,
            detail="Page must be greater than 0"
        )

    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 100"
        )

    query = db.query(Employee).filter(
        Employee.is_active == True
    )

    # Search by name, email, or employee code
    if search:
        query = query.filter(
            (Employee.name.ilike(f"%{search}%"))
            | (Employee.email.ilike(f"%{search}%"))
            | (Employee.employee_code.ilike(f"%{search}%"))
        )

    # Filter by department
    if department_id:
        query = query.filter(
            Employee.department_id == department_id
        )

    # Sorting
    allowed_sort_fields = {
        "id": Employee.id,
        "name": Employee.name,
        "salary": Employee.salary,
        "date_of_joining": Employee.date_of_joining,
    }

    if sort_by not in allowed_sort_fields:
        raise HTTPException(
            status_code=400,
            detail="Invalid sort field"
        )

    sort_column = allowed_sort_fields[sort_by]

    if sort_order.lower() == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Pagination
    offset = (page - 1) * limit

    return query.offset(offset).limit(limit).all()


@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin", "HR", "Employee"))
):
    employee = db.query(Employee).filter(
        Employee.id == employee_id,
        Employee.is_active == True
    ).first()

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    # Employee role can view only their own record
    if current_user.role == "Employee":
        if current_user.employee_id != employee.id:
            raise HTTPException(
                status_code=403,
                detail="You can access only your own employee record"
            )

    return employee


@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    employee_id: int,
    data: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin", "HR"))
):
    employee = db.query(Employee).filter(
        Employee.id == employee_id
    ).first()

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    if data.date_of_joining and data.date_of_joining > date.today():
        raise HTTPException(
            status_code=400,
            detail="Date of joining cannot be in the future"
        )

    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(employee, key, value)

    db.commit()
    db.refresh(employee)

    return employee


@router.delete("/{employee_id}")
def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin", "HR"))
):
    employee = db.query(Employee).filter(
        Employee.id == employee_id
    ).first()

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    employee.is_active = False

    db.commit()

    return {
        "message": "Employee deactivated successfully"
    }
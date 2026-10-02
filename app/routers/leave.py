from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_roles
from app.database import get_db
from app.models.employee import Employee
from app.models.leave import Leave
from app.models.user import User
from app.schemas.leave import (
    LeaveCreate,
    LeaveResponse,
    LeaveStatusUpdate,
)

router = APIRouter(prefix="/leaves", tags=["Leaves"])


LEAVE_LIMITS = {
    "Sick": 12,
    "Casual": 10,
    "Earned": 15,
}


def calculate_weekdays(start_date: date, end_date: date) -> int:
    total = 0
    current = start_date

    while current <= end_date:
        if current.weekday() < 5:
            total += 1

        current += timedelta(days=1)

    return total


def get_used_leave_days(
    db: Session,
    employee_id: int,
    leave_type: str,
    year: int
) -> int:
    leaves = db.query(Leave).filter(
        Leave.employee_id == employee_id,
        Leave.leave_type == leave_type,
        Leave.status == "Approved"
    ).all()

    total = 0

    for leave in leaves:
        if leave.start_date.year == year:
            total += leave.total_days

    return total


def check_overlap(
    db: Session,
    employee_id: int,
    start_date: date,
    end_date: date
) -> bool:
    existing_leave = db.query(Leave).filter(
        Leave.employee_id == employee_id,
        Leave.status.in_(["Pending", "Approved"]),
        Leave.start_date <= end_date,
        Leave.end_date >= start_date
    ).first()

    return existing_leave is not None


@router.post(
    "",
    response_model=LeaveResponse,
    status_code=status.HTTP_201_CREATED
)
def apply_leave(
    data: LeaveCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.employee_id is None:
        raise HTTPException(
            status_code=400,
            detail="User is not linked to an employee"
        )

    employee = db.query(Employee).filter(
        Employee.id == current_user.employee_id
    ).first()

    if not employee or not employee.is_active:
        raise HTTPException(
            status_code=400,
            detail="Inactive employee cannot apply for leave"
        )

    if data.leave_type not in LEAVE_LIMITS:
        raise HTTPException(
            status_code=400,
            detail="Invalid leave type. Use Sick, Casual, or Earned"
        )

    if data.start_date < date.today():
        raise HTTPException(
            status_code=400,
            detail="Leave cannot start in the past"
        )

    if data.end_date < data.start_date:
        raise HTTPException(
            status_code=400,
            detail="End date cannot be before start date"
        )

    total_days = calculate_weekdays(
        data.start_date,
        data.end_date
    )

    if total_days <= 0:
        raise HTTPException(
            status_code=400,
            detail="Leave must contain at least one weekday"
        )

    if check_overlap(
        db,
        employee.id,
        data.start_date,
        data.end_date
    ):
        raise HTTPException(
            status_code=400,
            detail="Leave dates overlap with an existing leave request"
        )

    used_days = get_used_leave_days(
        db,
        employee.id,
        data.leave_type,
        data.start_date.year
    )

    available_days = LEAVE_LIMITS[data.leave_type] - used_days

    if total_days > available_days:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient {data.leave_type} leave balance"
        )

    leave = Leave(
        employee_id=employee.id,
        leave_type=data.leave_type,
        start_date=data.start_date,
        end_date=data.end_date,
        total_days=total_days,
        reason=data.reason,
        status="Pending"
    )

    db.add(leave)
    db.commit()
    db.refresh(leave)

    return leave


@router.get("/my", response_model=list[LeaveResponse])
def my_leaves(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.employee_id is None:
        raise HTTPException(
            status_code=400,
            detail="User is not linked to an employee"
        )

    return db.query(Leave).filter(
        Leave.employee_id == current_user.employee_id
    ).all()


@router.get("", response_model=list[LeaveResponse])
def get_all_leaves(
    page: int = 1,
    limit: int = 10,
    search: str | None = None,
    leave_type: str | None = None,
    leave_status: str | None = None,
    employee_id: int | None = None,
    sort_by: str = "id",
    sort_order: str = "asc",
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Admin", "HR"))
):
    # Pagination validation
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

    query = db.query(Leave)

    # Search by reason
    if search:
        query = query.filter(
            Leave.reason.ilike(f"%{search}%")
        )

    # Filter by leave type
    if leave_type:
        if leave_type not in LEAVE_LIMITS:
            raise HTTPException(
                status_code=400,
                detail="Invalid leave type. Use Sick, Casual, or Earned"
            )

        query = query.filter(
            Leave.leave_type == leave_type
        )

    # Filter by status
    if leave_status:
        allowed_statuses = [
            "Pending",
            "Approved",
            "Rejected",
            "Cancelled"
        ]

        if leave_status not in allowed_statuses:
            raise HTTPException(
                status_code=400,
                detail="Invalid leave status"
            )

        query = query.filter(
            Leave.status == leave_status
        )

    # Filter by employee
    if employee_id:
        query = query.filter(
            Leave.employee_id == employee_id
        )

    # Sorting
    allowed_sort_fields = {
        "id": Leave.id,
        "start_date": Leave.start_date,
        "end_date": Leave.end_date,
        "total_days": Leave.total_days,
        "created_at": Leave.created_at
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


@router.put("/{leave_id}/approve", response_model=LeaveResponse)
def approve_leave(
    leave_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Admin", "HR"))
):
    leave = db.query(Leave).filter(
        Leave.id == leave_id
    ).first()

    if not leave:
        raise HTTPException(
            status_code=404,
            detail="Leave request not found"
        )

    if leave.status != "Pending":
        raise HTTPException(
            status_code=400,
            detail="Only Pending leave can be approved"
        )

    if (
        current_user.role == "HR"
        and current_user.employee_id == leave.employee_id
    ):
        raise HTTPException(
            status_code=403,
            detail="HR cannot approve their own leave"
        )

    leave.status = "Approved"
    leave.approved_by = current_user.employee_id

    db.commit()
    db.refresh(leave)

    return leave


@router.put("/{leave_id}/reject", response_model=LeaveResponse)
def reject_leave(
    leave_id: int,
    data: LeaveStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Admin", "HR"))
):
    leave = db.query(Leave).filter(
        Leave.id == leave_id
    ).first()

    if not leave:
        raise HTTPException(
            status_code=404,
            detail="Leave request not found"
        )

    if leave.status != "Pending":
        raise HTTPException(
            status_code=400,
            detail="Only Pending leave can be rejected"
        )

    if (
        current_user.role == "HR"
        and current_user.employee_id == leave.employee_id
    ):
        raise HTTPException(
            status_code=403,
            detail="HR cannot reject their own leave"
        )

    if not data.rejection_reason:
        raise HTTPException(
            status_code=400,
            detail="Rejection reason is required"
        )

    leave.status = "Rejected"
    leave.rejection_reason = data.rejection_reason
    leave.approved_by = current_user.employee_id

    db.commit()
    db.refresh(leave)

    return leave


@router.put("/{leave_id}/cancel", response_model=LeaveResponse)
def cancel_leave(
    leave_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    leave = db.query(Leave).filter(
        Leave.id == leave_id
    ).first()

    if not leave:
        raise HTTPException(
            status_code=404,
            detail="Leave request not found"
        )

    if leave.status != "Pending":
        raise HTTPException(
            status_code=400,
            detail="Only Pending leave can be cancelled"
        )

    if current_user.employee_id != leave.employee_id:
        raise HTTPException(
            status_code=403,
            detail="You can cancel only your own leave"
        )

    leave.status = "Cancelled"

    db.commit()
    db.refresh(leave)

    return leave
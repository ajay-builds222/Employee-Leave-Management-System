from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.database import get_db
from app.models.department import Department
from app.models.employee import Employee
from app.models.leave import Leave


router = APIRouter(
    prefix="/reports",
    tags=["Reports"]
)


LEAVE_LIMITS = {
    "Sick": 12,
    "Casual": 10,
    "Earned": 15,
}


@router.get("/dashboard")
def dashboard(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin", "HR"))
):
    total_employees = db.query(Employee).count()

    active_employees = db.query(Employee).filter(
        Employee.is_active == True
    ).count()

    inactive_employees = db.query(Employee).filter(
        Employee.is_active == False
    ).count()

    total_departments = db.query(Department).filter(
        Department.is_active == True
    ).count()

    pending_leaves = db.query(Leave).filter(
        Leave.status == "Pending"
    ).count()

    approved_leaves = db.query(Leave).filter(
        Leave.status == "Approved"
    ).count()

    rejected_leaves = db.query(Leave).filter(
        Leave.status == "Rejected"
    ).count()

    cancelled_leaves = db.query(Leave).filter(
        Leave.status == "Cancelled"
    ).count()

    return {
        "total_employees": total_employees,
        "active_employees": active_employees,
        "inactive_employees": inactive_employees,
        "total_departments": total_departments,
        "leave_summary": {
            "pending": pending_leaves,
            "approved": approved_leaves,
            "rejected": rejected_leaves,
            "cancelled": cancelled_leaves
        }
    }


@router.get("/leave-summary")
def leave_summary(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin", "HR"))
):
    employees = db.query(Employee).filter(
        Employee.is_active == True
    ).all()

    result = []

    for employee in employees:

        approved_leaves = db.query(Leave).filter(
            Leave.employee_id == employee.id,
            Leave.status == "Approved"
        ).all()

        used = {
            "Sick": 0,
            "Casual": 0,
            "Earned": 0
        }

        for leave in approved_leaves:
            if leave.leave_type in used:
                used[leave.leave_type] += leave.total_days

        result.append({
            "employee_id": employee.id,
            "employee_code": employee.employee_code,
            "employee_name": employee.name,
            "leave_balance": {
                "Sick": {
                    "used": used["Sick"],
                    "remaining": max(
                        LEAVE_LIMITS["Sick"] - used["Sick"], 0
                    )
                },
                "Casual": {
                    "used": used["Casual"],
                    "remaining": max(
                        LEAVE_LIMITS["Casual"] - used["Casual"], 0
                    )
                },
                "Earned": {
                    "used": used["Earned"],
                    "remaining": max(
                        LEAVE_LIMITS["Earned"] - used["Earned"], 0
                    )
                }
            }
        })

    return result
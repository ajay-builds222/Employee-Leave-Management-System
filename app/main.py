from fastapi import FastAPI

from app.routers.auth import router as auth_router
from app.routers.department import router as department_router
from app.routers.employee import router as employee_router
from app.routers.leave import router as leave_router
from app.routers.report import router as report_router


app = FastAPI(
    title="Employee & Leave Management System"
)


app.include_router(auth_router)
app.include_router(department_router)
app.include_router(employee_router)
app.include_router(leave_router)
app.include_router(report_router)


@app.get("/")
def root():
    return {
        "message": "Employee & Leave Management System API is running"
    }
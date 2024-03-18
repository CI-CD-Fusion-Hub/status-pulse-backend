from typing import List

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.schemas.notifications_sch import CreateNotification, UpdateNotification, NotificationOut
from app.schemas.response_sch import Response
from app.services.notifications_srv import NotificationService
from app.utils.check_session import auth_required
from app.utils.database import get_db

router = APIRouter()


def create_notification_service(db: Session = Depends(get_db)):
    return NotificationService(db)


@router.get("/notifications", tags=["notifications"])
@auth_required
async def get_all(request: Request, notification_service: NotificationService = Depends(create_notification_service)) \
        -> List[NotificationOut]:
    return await notification_service.get_all(request)


@router.get("/notifications/{notification_id}", tags=["notifications"])
@auth_required
async def get_by_id(request: Request, notification_id: int, notification_service: NotificationService = Depends(
                    create_notification_service)) -> NotificationOut:
    return await notification_service.get_by_id(request, notification_id)


@router.post("/notifications", tags=["notifications"])
@auth_required
async def create(request: Request, notification_data: CreateNotification,
                 notification_service: NotificationService = Depends(create_notification_service)) -> NotificationOut:
    return await notification_service.create_notification(request, notification_data)


@router.put("/notifications/{notification_id}", tags=["notifications"])
@auth_required
async def update(request: Request, notification_id: int, notification_data: UpdateNotification,
                 notification_service: NotificationService = Depends(create_notification_service)) -> NotificationOut:
    return await notification_service.update_notification(request, notification_id, notification_data)


@router.delete("/notifications/{notification_id}", tags=["notifications"])
@auth_required
async def delete(request: Request, notification_id: int,
                 notification_service: NotificationService = Depends(create_notification_service)) -> Response:
    return await notification_service.delete_notification(request, notification_id)

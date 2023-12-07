from typing import List

from fastapi import APIRouter, Depends, Request, Query

from app.schemas.dashboards_sch import DashboardOut, CreateDashboard, UpdateDashboard
from app.schemas.response_sch import Response
from app.services.dashboards_srv import DashboardService
from app.utils.check_session import auth_required

router = APIRouter()


def create_dashboard_service():
    return DashboardService()


@router.get("/dashboards", tags=["dashboards"])
@auth_required
async def get_all(request: Request, dashboard_service: DashboardService = Depends(create_dashboard_service)) \
        -> List[DashboardOut]:
    return await dashboard_service.get_all(request)


@router.get("/dashboards/{dashboard_id}", tags=["dashboards"])
@auth_required
async def get_by_id(request: Request, dashboard_id: int, dashboard_service: DashboardService = Depends(
                    create_dashboard_service)) -> DashboardOut:
    return await dashboard_service.get_by_id(request, dashboard_id)


@router.get("/dashboard", tags=["dashboards"])
@auth_required
async def get_by_id(request: Request, name: str = Query(None), dashboard_service: DashboardService = Depends(
                    create_dashboard_service)) -> DashboardOut:
    return await dashboard_service.get_by_uuid(request, name)


@router.post("/dashboards", tags=["dashboards"])
@auth_required
async def create(request: Request, dashboard_data: CreateDashboard,
                 dashboards_service: DashboardService = Depends(create_dashboard_service)) -> DashboardOut:
    return await dashboards_service.create_dashboard(request, dashboard_data)


@router.put("/dashboards/{dashboard_id}", tags=["dashboards"])
@auth_required
async def update(request: Request, dashboard_id: int, dashboard_data: UpdateDashboard,
                 dashboards_service: DashboardService = Depends(create_dashboard_service)) -> DashboardOut:
    return await dashboards_service.update_dashboard(request, dashboard_id, dashboard_data)


@router.delete("/dashboards/{dashboard_id}", tags=["dashboards"])
@auth_required
async def delete(request: Request, dashboard_id: int,
                 dashboards_service: DashboardService = Depends(create_dashboard_service)) -> Response:
    return await dashboards_service.delete_dashboard(request, dashboard_id)

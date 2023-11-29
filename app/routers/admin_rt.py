from fastapi import APIRouter, Depends, Request

from app.schemas.endpoints_sch import UpdateEndpoint
from app.schemas.users_sch import UserResponse
from app.services.endpoints_srv import EndpointService
from app.utils.check_session import auth_required

router = APIRouter()


def create_endpoint_service():
    return EndpointService()


@router.get("/admin/endpoints", tags=["admin"])
@auth_required
async def get_all(request: Request,
                  endpoint_service: EndpointService = Depends(create_endpoint_service)) -> UserResponse:
    return await endpoint_service.get_all(request)


@router.get("/admin/endpoints/{endpoint_id}", tags=["admin"])
@auth_required
async def get_by_id(request: Request, endpoint_id: int,
                    endpoint_service: EndpointService = Depends(create_endpoint_service)) -> UserResponse:
    return await endpoint_service.get_by_id(request, endpoint_id)


@router.get("/admin/endpoints/{endpoint_id}/status", tags=["admin"])
@auth_required
async def get_status_graph_by_id(request: Request, endpoint_id: int,
                                 endpoint_service: EndpointService = Depends(create_endpoint_service)) -> UserResponse:
    return await endpoint_service.get_status_graph_by_id(request, endpoint_id)


@router.get("/admin/endpoints/{endpoint_id}/uptime", tags=["admin"])
@auth_required
async def get_status_graph_by_id(request: Request, endpoint_id: int,
                                 endpoint_service: EndpointService = Depends(create_endpoint_service)) -> UserResponse:
    return await endpoint_service.get_uptime_graph_by_id(request, endpoint_id)


@router.put("/admin/endpoints/{endpoint_id}", tags=["admin"])
@auth_required
async def update_endpoint(request: Request, endpoint_id: int, endpoint_data: UpdateEndpoint,
                          endpoint_service: EndpointService = Depends(create_endpoint_service)) -> UserResponse:
    return await endpoint_service.update_endpoint(request, endpoint_id, endpoint_data)


@router.delete("/admin/endpoints/{endpoint_id}", tags=["admin"])
@auth_required
async def delete_endpoint(request: Request, endpoint_id: int,
                          endpoint_service: EndpointService = Depends(create_endpoint_service)) -> UserResponse:
    return await endpoint_service.delete_endpoint(request, endpoint_id)
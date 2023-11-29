from fastapi import APIRouter, Depends, Request

from app.schemas.endpoints_sch import CreateEndpoint, UpdateEndpoint
from app.schemas.response_sch import Response
from app.schemas.users_sch import UserResponse
from app.services.auth_srv import AuthService
from app.services.endpoints_srv import EndpointService

router = APIRouter()


def create_endpoint_service():
    return EndpointService()


@router.get("/endpoints", tags=["endpoints"])
async def get_all(request: Request,
                  endpoint_service: EndpointService = Depends(create_endpoint_service)) -> UserResponse:
    return await endpoint_service.get_all(request)


@router.get("/endpoints/{endpoint_id}", tags=["endpoints"])
async def get_by_id(endpoint_id: int, request: Request,
                    endpoint_service: EndpointService = Depends(create_endpoint_service)) -> UserResponse:
    return await endpoint_service.get_by_id(request, endpoint_id)


@router.get("/endpoints/{endpoint_id}/status", tags=["endpoints"])
async def get_status_graph_by_id(endpoint_id: int, request: Request,
                                 endpoint_service: EndpointService = Depends(create_endpoint_service)) -> UserResponse:
    return await endpoint_service.get_status_graph_by_id(request, endpoint_id)


@router.get("/endpoints/{endpoint_id}/uptime", tags=["endpoints"])
async def get_status_graph_by_id(endpoint_id: int, request: Request,
                                 endpoint_service: EndpointService = Depends(create_endpoint_service)) -> UserResponse:
    return await endpoint_service.get_uptime_graph_by_id(request, endpoint_id)


@router.post("/endpoints", tags=["endpoints"])
async def create_endpoint(request: Request, endpoint_data: CreateEndpoint,
                          endpoint_service: EndpointService = Depends(create_endpoint_service)) -> UserResponse:
    return await endpoint_service.create_endpoint(request, endpoint_data)


@router.put("/endpoints/{endpoint_id}", tags=["endpoints"])
async def update_endpoint(request: Request, endpoint_id: int, endpoint_data: UpdateEndpoint,
                          endpoint_service: EndpointService = Depends(create_endpoint_service)) -> UserResponse:
    return await endpoint_service.update_endpoint(request, endpoint_id, endpoint_data)


@router.delete("/endpoints/{endpoint_id}", tags=["endpoints"])
async def delete_endpoint(request: Request, endpoint_id: int,
                          endpoint_service: EndpointService = Depends(create_endpoint_service)) -> UserResponse:
    return await endpoint_service.delete_endpoint(request, endpoint_id)

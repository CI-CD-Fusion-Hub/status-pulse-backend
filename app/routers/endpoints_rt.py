from fastapi import APIRouter, Depends, Request, Query

from app.schemas.endpoints_sch import CreateEndpoint, UpdateEndpoint, BaseEndpointsOut, EndpointsOut
from app.schemas.response_sch import Response
from app.schemas.shared_tokens_sch import CreateTokenBody
from app.services.endpoints_srv import EndpointService
from app.utils.check_session import auth_required

router = APIRouter()


def create_endpoint_service():
    return EndpointService()


@router.get("/endpoints", tags=["endpoints"])
@auth_required
async def get_all(request: Request,
                  endpoint_service: EndpointService = Depends(create_endpoint_service)) -> EndpointsOut:
    return await endpoint_service.get_all(request)


@router.get("/endpoints/share", tags=["endpoints"])
@auth_required
async def validate_shared_endpoint(request: Request,
                                   token: str = Query(None),
                                   endpoint_service: EndpointService = Depends(create_endpoint_service)) -> Response:
    return await endpoint_service.validate_shared_endpoint(request, token)


@router.get("/endpoints/{endpoint_id}", tags=["endpoints"])
@auth_required
async def get_by_id(request: Request, endpoint_id: int,
                    endpoint_service: EndpointService = Depends(create_endpoint_service)) -> BaseEndpointsOut:
    return await endpoint_service.get_by_id(request, endpoint_id)


@router.get("/endpoints/{endpoint_id}/status", tags=["endpoints"])
@auth_required
async def get_status_graph_by_id(request: Request, endpoint_id: int,
                                 endpoint_service: EndpointService =
                                 Depends(create_endpoint_service)) -> BaseEndpointsOut:
    return await endpoint_service.get_status_graph_by_id(request, endpoint_id)


@router.get("/endpoints/{endpoint_id}/uptime", tags=["endpoints"])
@auth_required
async def get_status_graph_by_id(request: Request, endpoint_id: int,
                                 endpoint_service: EndpointService = Depends(create_endpoint_service)) -> Response:
    return await endpoint_service.get_uptime_graph_by_id(request, endpoint_id)


@router.post("/endpoints/{endpoint_id}/share", tags=["endpoints"])
@auth_required
async def share_endpoint(request: Request, endpoint_id: int, exp_time: CreateTokenBody,
                         endpoint_service: EndpointService = Depends(create_endpoint_service)) -> Response:
    return await endpoint_service.share_endpoint(request, endpoint_id, exp_time.exp_time_minutes)


@router.post("/endpoints", tags=["endpoints"])
@auth_required
async def create_endpoint(request: Request, endpoint_data: CreateEndpoint,
                          endpoint_service: EndpointService = Depends(create_endpoint_service)) -> BaseEndpointsOut:
    return await endpoint_service.create_endpoint(request, endpoint_data)


@router.put("/endpoints/{endpoint_id}", tags=["endpoints"])
@auth_required
async def update_endpoint(request: Request, endpoint_id: int, endpoint_data: UpdateEndpoint,
                          endpoint_service: EndpointService = Depends(create_endpoint_service)) -> BaseEndpointsOut:
    return await endpoint_service.update_endpoint(request, endpoint_id, endpoint_data)


@router.delete("/endpoints/{endpoint_id}", tags=["endpoints"])
@auth_required
async def delete_endpoint(request: Request, endpoint_id: int,
                          endpoint_service: EndpointService = Depends(create_endpoint_service)) -> Response:
    return await endpoint_service.delete_endpoint(request, endpoint_id)

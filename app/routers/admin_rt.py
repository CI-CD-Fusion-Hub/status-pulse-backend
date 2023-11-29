from fastapi import APIRouter, Depends, Request

from app.schemas.endpoints_sch import UpdateEndpoint, BaseEndpointsOut, EndpointsOut
from app.schemas.response_sch import Response
from app.schemas.users_sch import UserResponse, UpdateUserProfile, UpdateUserAdmin
from app.services.endpoints_srv import EndpointService
from app.services.users_srv import UserService
from app.utils.check_session import auth_required, admin_access_required

router = APIRouter()


def create_endpoint_service():
    return EndpointService()


#############
# Endpoints #
#############

@router.get("/admin/endpoints", tags=["admin"])
@auth_required
async def get_all(request: Request,
                  endpoint_service: EndpointService = Depends(create_endpoint_service)) -> EndpointsOut:
    return await endpoint_service.get_all(request)


@router.get("/admin/endpoints/{endpoint_id}", tags=["admin"])
@auth_required
async def get_by_id(request: Request, endpoint_id: int,
                    endpoint_service: EndpointService = Depends(create_endpoint_service)) -> BaseEndpointsOut:
    return await endpoint_service.get_by_id(request, endpoint_id)


@router.get("/admin/endpoints/{endpoint_id}/status", tags=["admin"])
@auth_required
async def get_status_graph_by_id(request: Request, endpoint_id: int,
                                 endpoint_service: EndpointService = Depends(create_endpoint_service)) -> EndpointsOut:
    return await endpoint_service.get_status_graph_by_id(request, endpoint_id)


@router.get("/admin/endpoints/{endpoint_id}/uptime", tags=["admin"])
@auth_required
async def get_status_graph_by_id(request: Request, endpoint_id: int,
                                 endpoint_service: EndpointService = Depends(create_endpoint_service)) -> Response:
    return await endpoint_service.get_uptime_graph_by_id(request, endpoint_id)


@router.put("/admin/endpoints/{endpoint_id}", tags=["admin"])
@auth_required
async def update_endpoint(request: Request, endpoint_id: int, endpoint_data: UpdateEndpoint,
                          endpoint_service: EndpointService = Depends(create_endpoint_service)) -> BaseEndpointsOut:
    return await endpoint_service.update_endpoint(request, endpoint_id, endpoint_data)


@router.delete("/admin/endpoints/{endpoint_id}", tags=["admin"])
@auth_required
async def delete_endpoint(request: Request, endpoint_id: int,
                          endpoint_service: EndpointService = Depends(create_endpoint_service)) -> Response:
    return await endpoint_service.delete_endpoint(request, endpoint_id)


def create_user_service():
    return UserService()


#############
# Users #####
#############
@router.get("/admin/users", tags=["admin"])
@auth_required
@admin_access_required
async def get_all(request: Request,
                  user_service: UserService = Depends(create_user_service)):
    return await user_service.get_all()


@router.get("/admin/users/{user_id}", tags=["admin"])
@auth_required
@admin_access_required
async def get_by_id(request: Request, user_id: int,
                    user_service: UserService = Depends(create_user_service)) -> UserResponse:
    return await user_service.get_by_id(request, user_id)


@router.put("/admin/users/{user_id}", tags=["admin"])
@auth_required
@admin_access_required
async def update_user_profile(request: Request, user_id: int, user_data: UpdateUserAdmin,
                              user_service: UserService = Depends(create_user_service)) -> UserResponse:
    return await user_service.update_user(user_id, user_data)


@router.delete("/admin/users/{user_id}", tags=["admin"])
@auth_required
@admin_access_required
async def delete_user(request: Request, user_id: int,
                      user_service: UserService = Depends(create_user_service)) -> Response:
    return await user_service.delete_user(user_id)

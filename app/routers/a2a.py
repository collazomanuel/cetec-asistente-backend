from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.core.auth import get_current_admin
from app.models.auth import User
from app.models.a2a import A2AServer, A2AServerCreate, RoutingPolicy, RoutingPolicyUpdate
from app.services.a2a_service import A2AService
from app.core.database import get_database

router = APIRouter()

# Routing endpoints
@router.get("/routing/policy", response_model=RoutingPolicy, tags=["Routing"])
async def get_routing_policy(
    current_user: User = Depends(get_current_admin),
    db=Depends(get_database)
):
    """Get current routing policy (admin)"""
    a2a_service = A2AService(db)
    return await a2a_service.get_routing_policy()

@router.patch("/routing/policy", response_model=RoutingPolicy, tags=["Routing"])
async def update_routing_policy(
    policy_update: RoutingPolicyUpdate,
    current_user: User = Depends(get_current_admin),
    db=Depends(get_database)
):
    """Update routing policy (admin)"""
    a2a_service = A2AService(db)
    return await a2a_service.update_routing_policy(policy_update)

# A2A Server endpoints
@router.get("/a2a/servers", response_model=List[A2AServer], tags=["A2A"])
async def list_a2a_servers(
    current_user: User = Depends(get_current_admin),
    db=Depends(get_database)
):
    """List registered A2A servers (admin)"""
    a2a_service = A2AService(db)
    return await a2a_service.get_servers()

@router.post("/a2a/servers", response_model=A2AServer, status_code=status.HTTP_201_CREATED, tags=["A2A"])
async def create_a2a_server(
    server_data: A2AServerCreate,
    current_user: User = Depends(get_current_admin),
    db=Depends(get_database)
):
    """Register a new A2A server (admin)"""
    a2a_service = A2AService(db)
    return await a2a_service.create_server(server_data)

@router.get("/a2a/servers/{server_id}/health", tags=["A2A"])
async def check_a2a_server_health(
    server_id: str,
    current_user: User = Depends(get_current_admin),
    db=Depends(get_database)
):
    """A2A server health"""
    a2a_service = A2AService(db)
    health_data = await a2a_service.check_server_health(server_id)
    if not health_data:
        raise HTTPException(status_code=404, detail="A2A server not found")
    return health_data

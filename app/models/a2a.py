from pydantic import BaseModel
from typing import List, Optional, Dict

class A2AServer(BaseModel):
    id: str
    name: str
    base_url: str
    health: Optional[str] = "unknown"
    supports: List[str] = []

class A2AServerCreate(BaseModel):
    id: str
    name: str
    base_url: str
    supports: List[str] = []

class RoutingThresholds(BaseModel):
    confidence_min: float = 0.5

class RoutingPolicy(BaseModel):
    default_server_id: str
    bindings: Dict[str, str] = {}  # subject -> serverId
    thresholds: Optional[RoutingThresholds] = None

class RoutingPolicyUpdate(BaseModel):
    default_server_id: Optional[str] = None
    bindings: Optional[Dict[str, str]] = None
    thresholds: Optional[RoutingThresholds] = None

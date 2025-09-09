from typing import List, Optional, Dict, Any
from uuid import uuid4
import httpx
import time
from app.models.a2a import A2AServer, A2AServerCreate, RoutingPolicy, RoutingPolicyUpdate
from app.core.config import settings

class A2AService:
    def __init__(self, db):
        self.db = db
        self.servers_collection = db["a2a_servers"]
        self.routing_collection = db["routing_policy"]

    async def get_servers(self) -> List[A2AServer]:
        """Get all A2A servers"""
        cursor = self.servers_collection.find({})
        servers = []
        
        async for doc in cursor:
            server = A2AServer(
                id=str(doc["_id"]),
                name=doc["name"],
                base_url=doc["base_url"],
                health=doc.get("health", "unknown"),
                supports=doc.get("supports", [])
            )
            servers.append(server)
        
        return servers

    async def create_server(self, server_data: A2AServerCreate) -> A2AServer:
        """Create a new A2A server"""
        server_doc = {
            "_id": server_data.id,
            "name": server_data.name,
            "base_url": server_data.base_url,
            "health": "unknown",
            "supports": server_data.supports
        }
        
        await self.servers_collection.insert_one(server_doc)
        
        return A2AServer(
            id=server_data.id,
            name=server_data.name,
            base_url=server_data.base_url,
            health="unknown",
            supports=server_data.supports
        )

    async def check_server_health(self, server_id: str) -> Optional[Dict[str, Any]]:
        """Check health of an A2A server"""
        server_doc = await self.servers_collection.find_one({"_id": server_id})
        if not server_doc:
            return None
        
        try:
            start_time = time.time()
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{server_doc['base_url']}/health",
                    timeout=5.0
                )
                latency_ms = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    health_status = "ok"
                else:
                    health_status = "error"
                    
                # Update server health in database
                await self.servers_collection.update_one(
                    {"_id": server_id},
                    {"$set": {"health": health_status}}
                )
                
                return {
                    "status": health_status,
                    "latency_ms": latency_ms
                }
                
        except Exception:
            # Update server health to error
            await self.servers_collection.update_one(
                {"_id": server_id},
                {"$set": {"health": "error"}}
            )
            
            return {
                "status": "error",
                "latency_ms": None
            }

    async def get_routing_policy(self) -> RoutingPolicy:
        """Get current routing policy"""
        policy_doc = await self.routing_collection.find_one({"_id": "default"})
        
        if not policy_doc:
            # Create default policy
            default_policy = RoutingPolicy(
                default_server_id="default",
                bindings={},
                thresholds=None
            )
            
            await self.routing_collection.insert_one({
                "_id": "default",
                **default_policy.dict()
            })
            
            return default_policy
        
        return RoutingPolicy(
            default_server_id=policy_doc["default_server_id"],
            bindings=policy_doc.get("bindings", {}),
            thresholds=policy_doc.get("thresholds")
        )

    async def update_routing_policy(self, policy_update: RoutingPolicyUpdate) -> RoutingPolicy:
        """Update routing policy"""
        update_data = {k: v for k, v in policy_update.dict().items() if v is not None}
        
        await self.routing_collection.update_one(
            {"_id": "default"},
            {"$set": update_data},
            upsert=True
        )
        
        return await self.get_routing_policy()

    async def get_server_for_subject(self, subject: Optional[str] = None) -> str:
        """Get the appropriate A2A server for a subject"""
        policy = await self.get_routing_policy()
        
        if subject and subject in policy.bindings:
            return policy.bindings[subject]
        
        return policy.default_server_id

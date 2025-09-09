from typing import List, Optional
from uuid import uuid4
from datetime import datetime
from app.models.auth import User
from app.models.ingestion import (
    IngestionRequest, IngestionJob, IngestionStatus, IngestionMode
)

class IngestionService:
    def __init__(self, db):
        self.db = db
        self.collection = db["ingestion_jobs"]

    async def start_ingestion(
        self,
        subject_slug: str,
        ingestion_request: IngestionRequest,
        user: User
    ) -> IngestionJob:
        """Start an ingestion job"""
        job_id = str(uuid4())
        
        # Count documents to process
        docs_query = {"subject_slug": subject_slug}
        if ingestion_request.mode == IngestionMode.SELECTED and ingestion_request.doc_ids:
            docs_query["_id"] = {"$in": ingestion_request.doc_ids}
        
        docs_collection = self.db["documents"]
        docs_total = await docs_collection.count_documents(docs_query)
        
        # Create job record
        job_doc = {
            "_id": job_id,
            "subject_slug": subject_slug,
            "status": IngestionStatus.QUEUED.value,
            "docs_total": docs_total,
            "docs_done": 0,
            "vectors": 0,
            "logs_url": None,
            "created_at": datetime.utcnow(),
            "created_by": user.id,
            "request": ingestion_request.dict()
        }
        
        await self.collection.insert_one(job_doc)
        
        # In a real implementation, you would queue this job for processing
        # For now, we'll just return the job
        
        return IngestionJob(
            job_id=job_id,
            subject_slug=subject_slug,
            status=IngestionStatus.QUEUED,
            docs_total=docs_total,
            docs_done=0,
            vectors=0,
            logs_url=None
        )

    async def get_ingestions_for_subject(
        self,
        subject_slug: str,
        user: User
    ) -> List[IngestionJob]:
        """Get ingestion jobs for a subject"""
        cursor = self.collection.find(
            {"subject_slug": subject_slug}
        ).sort("created_at", -1)
        
        jobs = []
        async for doc in cursor:
            job = IngestionJob(
                job_id=str(doc["_id"]),
                subject_slug=doc["subject_slug"],
                status=IngestionStatus(doc["status"]),
                docs_total=doc["docs_total"],
                docs_done=doc["docs_done"],
                vectors=doc["vectors"],
                logs_url=doc.get("logs_url")
            )
            jobs.append(job)
        
        return jobs

    async def get_ingestion_job(
        self,
        job_id: str,
        user: User
    ) -> Optional[IngestionJob]:
        """Get a specific ingestion job"""
        doc = await self.collection.find_one({"_id": job_id})
        
        if not doc:
            return None
        
        return IngestionJob(
            job_id=str(doc["_id"]),
            subject_slug=doc["subject_slug"],
            status=IngestionStatus(doc["status"]),
            docs_total=doc["docs_total"],
            docs_done=doc["docs_done"],
            vectors=doc["vectors"],
            logs_url=doc.get("logs_url")
        )

    async def cancel_ingestion(
        self,
        job_id: str,
        user: User
    ) -> bool:
        """Cancel an ingestion job"""
        result = await self.collection.update_one(
            {
                "_id": job_id,
                "status": {"$in": [IngestionStatus.QUEUED.value, IngestionStatus.RUNNING.value]}
            },
            {"$set": {"status": IngestionStatus.CANCELED.value}}
        )
        
        # In a real implementation, you would also signal the worker to stop
        
        return result.modified_count > 0

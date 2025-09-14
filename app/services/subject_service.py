from typing import List, Optional
from uuid import uuid4
from app.models.auth import User
from app.models.subjects import Subject, SubjectCreate, SubjectUpdate

class SubjectService:
    def __init__(self, db):
        self.db = db
        self.collection = db["subjects"]

    async def create_subject(self, subject_data: SubjectCreate, user: User) -> Subject:
        """Create a new subject"""
        subject_doc = {
            "_id": str(uuid4()),
            "name": subject_data.name,
            "slug": subject_data.slug,
            "s3_bucket": subject_data.s3_bucket,
            "s3_prefix": subject_data.s3_prefix,
            "vector_collection": subject_data.vector_collection,
            "a2a_server_id": subject_data.a2a_server_id,
            "created_by": user.id
        }
        
        await self.collection.insert_one(subject_doc)
        
        return Subject(
            id=subject_doc["_id"],
            name=subject_doc["name"],
            slug=subject_doc["slug"],
            s3_bucket=subject_doc["s3_bucket"],
            s3_prefix=subject_doc["s3_prefix"],
            vector_collection=subject_doc["vector_collection"],
            a2a_server_id=subject_doc["a2a_server_id"],
        )

    async def get_subjects_for_user(self, user: User) -> List[Subject]:
        """Get subjects visible to the user based on their role"""
        # Admin can see all subjects
        # Teachers can see subjects they created or are assigned to
        # Students can see public subjects or those they're enrolled in
        
        query = {}
        if "admin" not in user.roles:
            # For now, return all subjects. In a real app, implement proper filtering
            pass
            
        cursor = self.collection.find(query)
        subjects = []
        async for doc in cursor:            
            subject = Subject(
                id=str(doc["_id"]),
                name=doc["name"],
                slug=doc["slug"],
                s3_bucket=doc["s3_bucket"],
                s3_prefix=doc["s3_prefix"],
                vector_collection=doc["vector_collection"],
                a2a_server_id=doc["a2a_server_id"],
            )
            subjects.append(subject)
        
        return subjects

    async def get_subject_by_slug(self, slug: str, user: User) -> Optional[Subject]:
        """Get a subject by slug"""
        doc = await self.collection.find_one({"slug": slug})
        if not doc:
            return None
            
        return Subject(
            id=str(doc["_id"]),
            name=doc["name"],
            slug=doc["slug"],
            s3_bucket=doc["s3_bucket"],
            s3_prefix=doc["s3_prefix"],
            vector_collection=doc["vector_collection"],
            a2a_server_id=doc["a2a_server_id"],
        )

    async def update_subject(
        self, 
        slug: str, 
        subject_update: SubjectUpdate, 
        user: User
    ) -> Optional[Subject]:
        """Update a subject"""
        update_data = {k: v for k, v in subject_update.dict().items() if v is not None}
        
        if not update_data:
            return await self.get_subject_by_slug(slug, user)
            
        result = await self.collection.update_one(
            {"slug": slug},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            return None
            
        return await self.get_subject_by_slug(slug, user)

    async def delete_subject(self, slug: str, user: User) -> bool:
        """Delete a subject"""
        result = await self.collection.delete_one({"slug": slug})
        return result.deleted_count > 0

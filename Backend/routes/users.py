from fastapi import APIRouter, Depends
from Backend.core.security import get_current_user
from Backend.schemas.user import UserCreate, UserLogin, Token, UserResponse, UserProfileUpdate
from Backend.schemas.analytics import DashboardResponse
from Backend.services import user_service, analytics_service

router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate):
    return await user_service.register_user(user)


@router.post("/login")
async def login(user: UserLogin):
    return await user_service.login_user(user)


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: str = Depends(get_current_user)):
    return await user_service.get_user_by_id(current_user)


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(current_user: str = Depends(get_current_user)):
    return await analytics_service.get_dashboard_summary(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_profile(
    data: UserProfileUpdate,
    current_user: str = Depends(get_current_user)
):
    """Update optional profile fields: age, gender, location, preferred_language, reason_for_using_app."""
    return await user_service.update_user_profile(current_user, data)


from pydantic import BaseModel

class InfluenceEntry(BaseModel):
    topic: str
    content: str

@router.post("/influence")
def save_influence(entry: InfluenceEntry, current_user: str = Depends(get_current_user)):
    from rag_pipeline.indexer import memory_indexer
    from rag_pipeline.schemas import MemoryDocument, MemoryType
    
    doc = MemoryDocument(
        user_id=current_user,
        content=f"Influence Factor: {entry.topic}. Notes: {entry.content}",
        memory_type=MemoryType.emotional_state,
        source="dashboard_influence",
        importance=0.8
    )
    memory_indexer.ingest(doc)
    return {"status": "success", "message": "Influence entry indexed and saved."}

@router.get("/influence")
def get_influences(current_user: str = Depends(get_current_user)):
    from rag_pipeline.vector_store import vector_store_manager
    vector_store = vector_store_manager.get_vector_store(current_user)
    results = vector_store.get(where={"source": "dashboard_influence"})
    
    entries = []
    if results and results.get("documents"):
        for i in range(len(results["documents"])):
            content = results["documents"][i]
            metadata = results["metadatas"][i]
            
            topic = "General"
            notes = content
            if "Influence Factor:" in content and ". Notes:" in content:
                parts = content.split(". Notes:")
                topic = parts[0].replace("Influence Factor:", "").strip()
                notes = parts[1].strip()
            
            entries.append({
                "id": results["ids"][i],
                "topic": topic,
                "content": notes,
                "timestamp": metadata.get("timestamp", ""),
            })
            
    # Sort by timestamp descending
    entries.sort(key=lambda x: x["timestamp"], reverse=True)
    return {"entries": entries}

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.schemas.matching import TutorRecommendation
from backend.app.services.auth import get_current_user, require_role
from backend.app.modules.matching.service import get_student_recommendations

router = APIRouter(prefix="/api/matching", tags=["matching"])

@router.get(
    "/recommendations",
    response_model=List[TutorRecommendation],
    dependencies=[Depends(require_role("STUDENT"))]
)
async def fetch_matching_recommendations(
    learning_need_id: Optional[str] = Query(None, description="Optional LearningNeed ID for targeted recommendations"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    recommendations = await get_student_recommendations(
        db=db,
        student_user_id=current_user.id,
        learning_need_id=learning_need_id
    )
    return recommendations


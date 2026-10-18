# DELETE /me: "Delete my data" on the Trust screen (PLAN.md section 8).

from fastapi import APIRouter, Depends, Response

from backend.services import supabase

router = APIRouter()


@router.delete("/me", status_code=204)
async def delete_me(user_id: str = Depends(supabase.current_user)) -> Response:
    # Profile, feedback, mandates and the anonymous account. Photos are never stored.
    await supabase.delete_user(user_id)
    return Response(status_code=204)

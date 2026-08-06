from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.schemas.token import Token
from app.services import user as user_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(
    # OAuth2PasswordRequestForm reads form fields named "username" and
    # "password". We use email as the identifier, so the email goes in the
    # "username" field. Depends() with no argument = "fill this from the request."
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    user = await user_service.get_user_by_email(db, form_data.username)

    # Verify in ONE combined check, and return the SAME error whether the email
    # doesn't exist or the password is wrong. Distinguishing them would let an
    # attacker discover which emails are registered (user enumeration).
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Credentials good — issue a token carrying this user's id.
    access_token = create_access_token(subject=str(user.id))
    return Token(access_token=access_token, token_type="bearer")
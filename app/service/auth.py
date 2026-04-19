from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password, get_password_hash
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin


async def register_user(db: AsyncSession, user_in: UserCreate) -> User:
    result = await db.execute(
        select(User).where(User.email == user_in.email)
    )
    existing_user = result.scalar_one_or_none()
    
    # TODO: В production вынести в Domain Exceptions + Exception Handlers
    # чтобы отвязать бизнес-логику от HTTP-слоя.
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    hashed_password = get_password_hash(user_in.password)
    new_user = User(
        email=user_in.email,
        hashed_password=hashed_password
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user


async def authenticate_user(
    db: AsyncSession, 
    login_data: UserLogin
) -> User:
    result = await db.execute(
        select(User).where(User.email == login_data.email)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        # TODO: В production вынести в Domain Exceptions + Exception Handlers
        # чтобы отвязать бизнес-логику от HTTP-слоя.

    return user
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponse)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """创建用户配置"""
    db_user = User(
        name=user.name,
        description=user.description,
        system_prompt=user.system_prompt
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


@router.get("/", response_model=List[UserResponse])
async def list_users(db: AsyncSession = Depends(get_db)):
    """获取所有用户配置"""
    result = await db.execute(select(User))
    users = result.scalars().all()
    if not users:
        # 创建默认用户
        default_user = User(name="用户", description="默认用户", system_prompt="你是一个友善的参与者。")
        db.add(default_user)
        await db.commit()
        await db.refresh(default_user)
        return [default_user]
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """获取单个用户配置"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_update: UserCreate, db: AsyncSession = Depends(get_db)):
    """更新用户配置"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    user.name = user_update.name
    user.description = user_update.description
    user.system_prompt = user_update.system_prompt
    
    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """删除用户配置"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    await db.delete(user)
    await db.commit()
    
    return {"message": "用户已删除"}

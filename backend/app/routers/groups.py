from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import json
from app.database import get_db
from app.models import Group, GroupMember, GroupConversation, GroupMessage, Bot
from app.schemas import (
    GroupCreate, GroupUpdate, GroupResponse,
    GroupConversationCreate, GroupConversationResponse,
    GroupMessageCreate, GroupMessageResponse,
    GroupBotResponse
)

router = APIRouter(prefix="/groups", tags=["groups"])


# ==================== 群组管理 ====================

@router.post("/", response_model=GroupResponse)
async def create_group(request: GroupCreate, db: AsyncSession = Depends(get_db)):
    """创建群组"""
    # 创建群组
    group = Group(
        name=request.name,
        avatar_url=request.avatar_url or "",
        allow_self_responses=request.allow_self_responses,
        activation_strategy=request.activation_strategy,
        generation_mode=request.generation_mode,
        disabled_members=json.dumps(request.disabled_members),
        fav=request.fav,
        auto_mode_delay=request.auto_mode_delay,
        hide_muted_sprites=request.hide_muted_sprites,
        generation_mode_join_prefix=request.generation_mode_join_prefix,
        generation_mode_join_suffix=request.generation_mode_join_suffix
    )
    db.add(group)
    await db.commit()
    await db.refresh(group)
    
    # 添加成员
    for member in request.members:
        group_member = GroupMember(
            group_id=group.id,
            bot_id=member.bot_id,
            order_index=member.order_index
        )
        db.add(group_member)
    await db.commit()
    
    return await get_group_response(db, group)


@router.get("/", response_model=List[GroupResponse])
async def get_all_groups(db: AsyncSession = Depends(get_db)):
    """获取所有群组"""
    result = await db.execute(select(Group).order_by(Group.created_at.desc()))
    groups = result.scalars().all()
    return [await get_group_response(db, g) for g in groups]


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(group_id: int, db: AsyncSession = Depends(get_db)):
    """获取单个群组"""
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="群组不存在")
    return await get_group_response(db, group)


@router.put("/{group_id}", response_model=GroupResponse)
async def update_group(group_id: int, request: GroupUpdate, db: AsyncSession = Depends(get_db)):
    """更新群组"""
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="群组不存在")
    
    # 更新字段
    if request.name is not None:
        group.name = request.name
    if request.avatar_url is not None:
        group.avatar_url = request.avatar_url
    if request.allow_self_responses is not None:
        group.allow_self_responses = request.allow_self_responses
    if request.activation_strategy is not None:
        group.activation_strategy = request.activation_strategy
    if request.generation_mode is not None:
        group.generation_mode = request.generation_mode
    if request.disabled_members is not None:
        group.disabled_members = json.dumps(request.disabled_members)
    if request.fav is not None:
        group.fav = request.fav
    if request.auto_mode_delay is not None:
        group.auto_mode_delay = request.auto_mode_delay
    if request.hide_muted_sprites is not None:
        group.hide_muted_sprites = request.hide_muted_sprites
    if request.generation_mode_join_prefix is not None:
        group.generation_mode_join_prefix = request.generation_mode_join_prefix
    if request.generation_mode_join_suffix is not None:
        group.generation_mode_join_suffix = request.generation_mode_join_suffix
    
    # 更新成员
    if request.members is not None:
        # 删除旧成员
        result = await db.execute(
            select(GroupMember).where(GroupMember.group_id == group_id)
        )
        old_members = result.scalars().all()
        for m in old_members:
            await db.delete(m)
        
        # 添加新成员
        for member in request.members:
            group_member = GroupMember(
                group_id=group.id,
                bot_id=member.bot_id,
                order_index=member.order_index
            )
            db.add(group_member)
    
    await db.commit()
    await db.refresh(group)
    return await get_group_response(db, group)


@router.delete("/{group_id}")
async def delete_group(group_id: int, db: AsyncSession = Depends(get_db)):
    """删除群组"""
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="群组不存在")
    
    # 删除成员
    result = await db.execute(
        select(GroupMember).where(GroupMember.group_id == group_id)
    )
    members = result.scalars().all()
    for m in members:
        await db.delete(m)
    
    # 删除群聊会话和消息
    result = await db.execute(
        select(GroupConversation).where(GroupConversation.group_id == group_id)
    )
    conversations = result.scalars().all()
    for conv in conversations:
        result = await db.execute(
            select(GroupMessage).where(GroupMessage.conversation_id == conv.id)
        )
        messages = result.scalars().all()
        for msg in messages:
            await db.delete(msg)
        await db.delete(conv)
    
    await db.delete(group)
    await db.commit()
    return {"message": "群组已删除"}


# ==================== 群聊会话管理 ====================

@router.post("/conversation", response_model=GroupConversationResponse)
async def create_group_conversation(request: GroupConversationCreate, db: AsyncSession = Depends(get_db)):
    """创建群聊会话"""
    # 验证群组存在
    result = await db.execute(select(Group).where(Group.id == request.group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="群组不存在")
    
    conversation = GroupConversation(
        group_id=request.group_id,
        title=request.title or "群聊"
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return conversation


@router.get("/{group_id}/conversations", response_model=List[GroupConversationResponse])
async def get_group_conversations(group_id: int, db: AsyncSession = Depends(get_db)):
    """获取群组的所有会话"""
    result = await db.execute(
        select(GroupConversation)
        .where(GroupConversation.group_id == group_id)
        .order_by(GroupConversation.created_at.desc())
    )
    return result.scalars().all()


@router.get("/conversation/{conversation_id}", response_model=List[GroupMessageResponse])
async def get_group_conversation_messages(conversation_id: int, db: AsyncSession = Depends(get_db)):
    """获取群聊会话的消息"""
    result = await db.execute(
        select(GroupMessage)
        .where(GroupMessage.conversation_id == conversation_id)
        .order_by(GroupMessage.created_at)
    )
    return result.scalars().all()


@router.post("/message", response_model=GroupMessageResponse)
async def create_group_message(request: GroupMessageCreate, db: AsyncSession = Depends(get_db)):
    """创建群聊消息"""
    message = GroupMessage(
        conversation_id=request.conversation_id,
        role=request.role,
        content=request.content,
        sender_name=request.sender_name or "",
        bot_id=request.bot_id
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


@router.delete("/conversation/{conversation_id}")
async def delete_group_conversation(conversation_id: int, db: AsyncSession = Depends(get_db)):
    """删除群聊会话"""
    result = await db.execute(
        select(GroupConversation).where(GroupConversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 删除消息
    result = await db.execute(
        select(GroupMessage).where(GroupMessage.conversation_id == conversation_id)
    )
    messages = result.scalars().all()
    for msg in messages:
        await db.delete(msg)
    
    await db.delete(conversation)
    await db.commit()
    return {"message": "会话已删除"}


# ==================== 辅助函数 ====================

async def get_group_response(db: AsyncSession, group: Group) -> GroupResponse:
    """获取群组响应，包含成员信息"""
    # 获取成员
    result = await db.execute(
        select(GroupMember)
        .where(GroupMember.group_id == group.id)
        .order_by(GroupMember.order_index)
    )
    members = result.scalars().all()
    
    # 获取机器人信息
    bot_responses = []
    for member in members:
        result = await db.execute(select(Bot).where(Bot.id == member.bot_id))
        bot = result.scalar_one_or_none()
        if bot:
            bot_responses.append(GroupBotResponse(
                id=bot.id,
                name=bot.name,
                description=bot.description,
                avatar=bot.avatar,
                talkativeness=bot.talkativeness
            ))
    
    # 解析disabled_members
    disabled = []
    try:
        disabled = json.loads(group.disabled_members) if group.disabled_members else []
    except:
        disabled = []
    
    return GroupResponse(
        id=group.id,
        name=group.name,
        avatar_url=group.avatar_url,
        allow_self_responses=group.allow_self_responses,
        activation_strategy=group.activation_strategy,
        generation_mode=group.generation_mode,
        disabled_members=disabled,
        fav=group.fav,
        auto_mode_delay=group.auto_mode_delay,
        hide_muted_sprites=group.hide_muted_sprites,
        generation_mode_join_prefix=group.generation_mode_join_prefix,
        generation_mode_join_suffix=group.generation_mode_join_suffix,
        created_at=group.created_at,
        updated_at=group.updated_at,
        members=bot_responses
    )

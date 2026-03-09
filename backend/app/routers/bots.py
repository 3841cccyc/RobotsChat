from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.database import get_db
from app.models import Bot, Conversation, Document
from app.schemas import BotCreate, BotUpdate, BotResponse, ConversationResponse, DocumentResponse
from app.services.rag_service import rag_service

router = APIRouter(prefix="/bots", tags=["bots"])


@router.post("/", response_model=BotResponse)
async def create_bot(bot: BotCreate, db: AsyncSession = Depends(get_db)):
    """创建新机器人"""
    db_bot = Bot(
        name=bot.name,
        description=bot.description,
        system_prompt=bot.system_prompt,
        model_name=bot.model_name,
        avatar=bot.avatar,
        temperature=bot.temperature,
        max_tokens=bot.max_tokens,
        talkativeness=bot.talkativeness
    )
    db.add(db_bot)
    await db.commit()
    await db.refresh(db_bot)
    return db_bot


@router.get("/", response_model=List[BotResponse])
async def list_bots(db: AsyncSession = Depends(get_db)):
    """获取所有机器人"""
    result = await db.execute(select(Bot))
    bots = result.scalars().all()
    return bots


@router.get("/{bot_id}", response_model=BotResponse)
async def get_bot(bot_id: int, db: AsyncSession = Depends(get_db)):
    """获取单个机器人"""
    result = await db.execute(select(Bot).where(Bot.id == bot_id))
    bot = result.scalar_one_or_none()
    if not bot:
        raise HTTPException(status_code=404, detail="机器人不存在")
    return bot


@router.put("/{bot_id}", response_model=BotResponse)
async def update_bot(bot_id: int, bot_update: BotUpdate, db: AsyncSession = Depends(get_db)):
    """更新机器人"""
    result = await db.execute(select(Bot).where(Bot.id == bot_id))
    bot = result.scalar_one_or_none()
    if not bot:
        raise HTTPException(status_code=404, detail="机器人不存在")
    
    # 更新字段
    update_data = bot_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(bot, field, value)
    
    await db.commit()
    await db.refresh(bot)
    return bot


@router.delete("/{bot_id}")
async def delete_bot(bot_id: int, db: AsyncSession = Depends(get_db)):
    """删除机器人"""
    result = await db.execute(select(Bot).where(Bot.id == bot_id))
    bot = result.scalar_one_or_none()
    if not bot:
        raise HTTPException(status_code=404, detail="机器人不存在")
    
    # 删除相关的向量库
    await rag_service.delete_vector_store(bot_id)
    
    # 先删除对话中的消息，再删除对话
    conv_result = await db.execute(select(Conversation).where(Conversation.bot_id == bot_id))
    conversations = conv_result.scalars().all()
    for conv in conversations:
        # 删除该对话的所有消息
        from app.models import Message
        msg_result = await db.execute(select(Message).where(Message.conversation_id == conv.id))
        messages = msg_result.scalars().all()
        for msg in messages:
            await db.delete(msg)
        # 删除对话
        await db.delete(conv)
    
    # 删除文档记录
    doc_result = await db.execute(select(Document).where(Document.bot_id == bot_id))
    documents = doc_result.scalars().all()
    for doc in documents:
        await db.delete(doc)
    
    await db.delete(bot)
    await db.commit()
    
    return {"message": "机器人已删除"}


@router.get("/{bot_id}/conversations", response_model=List[ConversationResponse])
async def get_bot_conversations(bot_id: int, db: AsyncSession = Depends(get_db)):
    """获取机器人的所有对话"""
    result = await db.execute(
        select(Conversation).where(Conversation.bot_id == bot_id).order_by(Conversation.updated_at.desc())
    )
    conversations = result.scalars().all()
    return conversations


@router.get("/{bot_id}/documents", response_model=List[DocumentResponse])
async def get_bot_documents(bot_id: int, db: AsyncSession = Depends(get_db)):
    """获取机器人的所有文档"""
    result = await db.execute(
        select(Document).where(Document.bot_id == bot_id).order_by(Document.created_at.desc())
    )
    documents = result.scalars().all()
    return documents

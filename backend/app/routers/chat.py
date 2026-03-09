from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.database import get_db
from app.models import Bot, Conversation, Message
from app.schemas import ChatRequest, ChatResponse, MessageResponse
from app.services.llm_service import llm_service
from app.services.rag_service import rag_service

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """发送消息并获取回复"""
    
    print(f"[DEBUG] 收到聊天请求: bot_id={request.bot_id}, use_docs={request.use_docs}")
    print(f"[DEBUG] api_config: {request.api_config}")
    
    # 获取机器人
    result = await db.execute(select(Bot).where(Bot.id == request.bot_id))
    bot = result.scalar_one_or_none()
    if not bot:
        raise HTTPException(status_code=404, detail="机器人不存在")
    
    print(f"[DEBUG] 机器人: {bot.name}, model_name: {bot.model_name}")
    
    # 获取或创建会话
    if request.conversation_id:
        conv_result = await db.execute(
            select(Conversation).where(Conversation.id == request.conversation_id)
        )
        conversation = conv_result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(status_code=404, detail="会话不存在")
    else:
        # 创建新会话
        conversation = Conversation(
            bot_id=bot.id,
            title=request.message[:50] + "..." if len(request.message) > 50 else request.message
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
    
    # 获取历史消息
    msg_result = await db.execute(
        select(Message).where(Message.conversation_id == conversation.id)
    )
    history_messages = msg_result.scalars().all()
    
    # 转换为消息格式
    messages = [{"role": msg.role, "content": msg.content} for msg in history_messages]
    
    # 添加当前消息
    messages.append({"role": "user", "content": request.message})
    
    # 保存用户消息
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.message
    )
    db.add(user_message)
    await db.commit()
    
    # 获取文档上下文（如果需要）
    docs_context = ""
    if request.use_docs:
        docs_context = await rag_service.similarity_search(bot.id, request.message, k=4)
    
    print(f"[DEBUG] 调用 LLM: 使用固定的 MiniMax 配置, messages 数量: {len(messages)}")
    
    try:
        # 调用 LLM（使用固定的 MiniMax 配置）
        # 传入所有消息（包括当前用户消息）
        if docs_context:
            response = await llm_service.chat_with_docs(
                messages=messages,
                system_prompt=bot.system_prompt,
                docs_context=docs_context,
                temperature=bot.temperature,
                max_tokens=bot.max_tokens,
                learned_context=conversation.learned_context
            )
        else:
            response = await llm_service.chat(
                messages=messages,
                system_prompt=bot.system_prompt,
                temperature=bot.temperature,
                max_tokens=bot.max_tokens,
                learned_context=conversation.learned_context
            )
        
        print(f"[DEBUG] LLM 响应成功: {response[:100]}...")
    except Exception as e:
        print(f"[ERROR] LLM 调用失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI 调用失败: {str(e)}")
    
    # 保存助手回复
    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=response
    )
    db.add(assistant_message)
    await db.commit()
    await db.refresh(assistant_message)
    
    # 更新会话时间
    conversation.updated_at = Message.created_at
    await db.commit()
    
    return ChatResponse(
        message=response,
        conversation_id=conversation.id,
        message_id=assistant_message.id
    )


@router.get("/conversation/{conversation_id}", response_model=List[MessageResponse])
async def get_conversation_messages(conversation_id: int, db: AsyncSession = Depends(get_db)):
    """获取会话的所有消息"""
    result = await db.execute(
        select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at)
    )
    messages = result.scalars().all()
    return messages


@router.delete("/conversation/{conversation_id}")
async def delete_conversation(conversation_id: int, db: AsyncSession = Depends(get_db)):
    """删除会话"""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 删除所有消息
    msg_result = await db.execute(
        select(Message).where(Message.conversation_id == conversation_id)
    )
    messages = msg_result.scalars().all()
    for msg in messages:
        await db.delete(msg)
    
    await db.delete(conversation)
    await db.commit()
    
    return {"message": "会话已删除"}

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import json
import asyncio
from app.database import get_db
from app.models import Bot, GroupConversation, GroupMessage
from app.schemas import (
    GroupChatStartRequest, 
    GroupChatMessageRequest, 
    GroupChatResponse,
    MessageResponse
)
from app.services.group_chat_service import group_chat_service, auto_chat_rounds
from app.services.rag_service import rag_service

router = APIRouter(prefix="/group-chat", tags=["group-chat"])


@router.post("/start", response_model=GroupChatResponse)
async def start_group_chat(request: GroupChatStartRequest, db: AsyncSession = Depends(get_db)):
    """启动群聊（带用户首条消息）"""
    
    print(f"[DEBUG] 收到群聊请求: bot_ids={request.bot_ids}, user_name={request.user_name}")
    
    try:
        # 获取所有机器人
        bots = []
        for bot_id in request.bot_ids:
            result = await db.execute(select(Bot).where(Bot.id == bot_id))
            bot = result.scalar_one_or_none()
            if bot:
                bots.append(bot)
        
        if not bots:
            raise HTTPException(status_code=400, detail="没有有效的机器人")
        
        # 创建群聊会话
        conversation = GroupConversation(
            title=request.topic or "群聊",
            bot_id=bots[0].id
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        
        # 如果有用户消息，保存
        if request.user_prompt:
            user_message = GroupMessage(
                conversation_id=conversation.id,
                role="user",
                content=request.user_prompt,
                sender_name=request.user_name or "用户"
            )
            db.add(user_message)
            await db.commit()
        
        # 收集所有消息
        all_messages = []
        if request.user_prompt:
            all_messages.append({
                "role": "user",
                "content": request.user_prompt,
                "sender_name": request.user_name or "用户"
            })
        
        # 让每个机器人依次回复
        for bot in bots:
            # 获取上下文
            bot_messages = group_chat_service._get_bot_context(all_messages, bot.name)
            
            # 生成回复
            try:
                response = group_chat_service._generate_bot_response_stream(
                    bot=bot,
                    messages=bot_messages,
                    all_messages=all_messages
                )
                
                # 收集完整响应
                full_response = ""
                async for chunk in response:
                    full_response += chunk
                
                # 保存消息
                if full_response:
                    bot_message = GroupMessage(
                        conversation_id=conversation.id,
                        role="assistant",
                        content=full_response,
                        sender_name=bot.name
                    )
                    db.add(bot_message)
                    await db.commit()
                    
                    all_messages.append({
                        "role": "assistant",
                        "content": full_response,
                        "sender_name": bot.name,
                        "bot_id": bot.id
                    })
                    
            except Exception as e:
                print(f"Error generating response for {bot.name}: {e}")
                all_messages.append({
                    "role": "assistant",
                    "content": "抱歉，我遇到了一些问题。",
                    "sender_name": bot.name,
                    "bot_id": bot.id,
                    "error": str(e)
                })
            
            await asyncio.sleep(0.5)
        
        print(f"[DEBUG] 群聊生成了 {len(all_messages)} 条消息")
        
        return GroupChatResponse(
            messages=all_messages,
            conversation_id=conversation.id
        )
        
    except ValueError as e:
        print(f"[ERROR] 群聊启动失败 (ValueError): {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"[ERROR] 群聊启动失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"群聊启动失败: {str(e)}")


@router.post("/start-stream")
async def start_group_chat_stream(request: GroupChatStartRequest, db: AsyncSession = Depends(get_db)):
    """启动群聊（流式输出）"""
    
    print(f"[DEBUG] 收到群聊请求(流式): bot_ids={request.bot_ids}, user_name={request.user_name}")
    
    async def event_generator():
        try:
            # 获取所有机器人
            bots = []
            for bot_id in request.bot_ids:
                result = await db.execute(select(Bot).where(Bot.id == bot_id))
                bot = result.scalar_one_or_none()
                if bot:
                    bots.append(bot)
            
            if not bots:
                yield f"data: {json.dumps({'error': '没有有效的机器人'})}\n\n"
                return
            
            # 创建群聊会话
            conversation = GroupConversation(
                title=request.topic or "群聊",
                bot_id=bots[0].id
            )
            db.add(conversation)
            await db.commit()
            await db.refresh(conversation)
            
            # 保存用户消息
            messages = []
            if request.user_prompt:
                user_message = GroupMessage(
                    conversation_id=conversation.id,
                    role="user",
                    content=request.user_prompt,
                    sender_name=request.user_name or "用户"
                )
                db.add(user_message)
                await db.commit()
                
                messages.append({
                    "role": "user",
                    "content": request.user_prompt,
                    "sender_name": request.user_name or "用户"
                })
                
                yield f"data: {json.dumps({'type': 'user_message', 'content': request.user_prompt, 'sender_name': request.user_name or '用户'})}\n\n"
            
            # 让每个机器人依次回复
            for bot in bots:
                bot_messages = group_chat_service._get_bot_context(messages, bot.name)
                
                # 发送机器人开始信号
                yield f"data: {json.dumps({'type': 'bot_start', 'bot_name': bot.name, 'bot_id': bot.id})}\n\n"
                
                # 流式生成
                full_response = ""
                response_stream = group_chat_service._generate_bot_response_stream(
                    bot=bot,
                    messages=bot_messages,
                    all_messages=messages
                )
                
                async for chunk in response_stream:
                    # 改进的去重逻辑：基于累积内容进行检查
                    cleaned_chunk = chunk

                    # 检查新 chunk 是否以累积内容结尾（修正型输出）
                    if full_response and chunk.startswith(full_response[-50:] if len(full_response) > 50 else full_response):
                        # 新 chunk 是累积内容的延续，去除重叠部分
                        overlap_len = len(full_response[-50:] if len(full_response) > 50 else full_response)
                        cleaned_chunk = chunk[overlap_len:]
                    elif full_response and full_response in chunk:
                        # 新 chunk 完全包含之前内容（如修正输出），只取新增部分
                        # 使用 replace 只替换一次，避免错误替换
                        cleaned_chunk = chunk.replace(full_response, '', 1)

                    if cleaned_chunk:
                        full_response += cleaned_chunk
                        yield f"data: {json.dumps({'type': 'chunk', 'bot_name': bot.name, 'content': cleaned_chunk})}\n\n"
                
                # 后处理：去重和拆分
                final_response, should_split = group_chat_service._deduplicate_and_split(full_response)
                
                # 如果需要拆分，发送拆分信号
                if should_split and final_response:
                    short_messages = group_chat_service._split_into_short_messages(final_response)
                    if len(short_messages) > 1:
                        yield f"data: {json.dumps({'type': 'message_split', 'bot_name': bot.name, 'count': len(short_messages)})}\n\n"
                
                # 保存消息
                if final_response:
                    bot_message = GroupMessage(
                        conversation_id=conversation.id,
                        role="assistant",
                        content=final_response,
                        sender_name=bot.name
                    )
                    db.add(bot_message)
                    await db.commit()
                    
                    messages.append({
                        "role": "assistant",
                        "content": final_response,
                        "sender_name": bot.name,
                        "bot_id": bot.id
                    })
                else:
                    final_response = "抱歉，我遇到了一些问题。"
                    yield f"data: {json.dumps({'type': 'chunk', 'bot_name': bot.name, 'content': final_response})}\n\n"
                
                yield f"data: {json.dumps({'type': 'bot_done', 'bot_name': bot.name})}\n\n"
                
                await asyncio.sleep(0.5)
            
            # 完成
            yield f"data: {json.dumps({'type': 'done', 'conversation_id': conversation.id})}\n\n"
            
        except Exception as e:
            print(f"[ERROR] 流式群聊失败: {str(e)}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/message-stream")
async def add_group_message_stream(request: GroupChatMessageRequest, db: AsyncSession = Depends(get_db)):
    """在群聊中添加用户消息（流式输出）"""
    
    async def event_generator():
        try:
            # 获取所有机器人
            bots = []
            for bot_id in request.bot_ids:
                result = await db.execute(select(Bot).where(Bot.id == bot_id))
                bot = result.scalar_one_or_none()
                if bot:
                    bots.append(bot)
            
            if not bots:
                yield f"data: {json.dumps({'error': '没有有效的机器人'})}\n\n"
                return
            
            # 获取历史消息
            result = await db.execute(
                select(GroupMessage).where(GroupMessage.conversation_id == request.conversation_id)
            )
            history_messages = result.scalars().all()
            
            all_messages = []
            for msg in history_messages:
                all_messages.append({
                    "role": msg.role,
                    "content": msg.content,
                    "sender_name": msg.sender_name or ""
                })
            
            # 保存用户消息
            user_message = GroupMessage(
                conversation_id=request.conversation_id,
                role="user",
                content=request.message,
                sender_name=request.user_name
            )
            db.add(user_message)
            await db.commit()
            
            all_messages.append({
                "role": "user",
                "content": request.message,
                "sender_name": request.user_name
            })
            
            yield f"data: {json.dumps({'type': 'user_message', 'content': request.message, 'sender_name': request.user_name})}\n\n"
            
            # 让所有机器人依次回复
            for bot in bots:
                bot_messages = group_chat_service._get_bot_context(all_messages, bot.name)
                
                yield f"data: {json.dumps({'type': 'bot_start', 'bot_name': bot.name, 'bot_id': bot.id})}\n\n"

                full_response = ""
                response_stream = group_chat_service._generate_bot_response_stream(
                    bot=bot,
                    messages=bot_messages,
                    all_messages=all_messages
                )
                
                async for chunk in response_stream:
                    # 改进的去重逻辑：基于累积内容进行检查
                    cleaned_chunk = chunk

                    # 检查新 chunk 是否以累积内容结尾（修正型输出）
                    if full_response and chunk.startswith(full_response[-50:] if len(full_response) > 50 else full_response):
                        # 新 chunk 是累积内容的延续，去除重叠部分
                        overlap_len = len(full_response[-50:] if len(full_response) > 50 else full_response)
                        cleaned_chunk = chunk[overlap_len:]
                    elif full_response and full_response in chunk:
                        # 新 chunk 完全包含之前内容（如修正输出），只取新增部分
                        cleaned_chunk = chunk.replace(full_response, '', 1)

                    if cleaned_chunk:
                        full_response += cleaned_chunk
                        yield f"data: {json.dumps({'type': 'chunk', 'bot_name': bot.name, 'content': cleaned_chunk})}\n\n"
                
                # 后处理：去重和拆分
                final_response, should_split = group_chat_service._deduplicate_and_split(full_response)
                
                if should_split and final_response:
                    short_messages = group_chat_service._split_into_short_messages(final_response)
                    if len(short_messages) > 1:
                        yield f"data: {json.dumps({'type': 'message_split', 'bot_name': bot.name, 'count': len(short_messages)})}\n\n"
                
                if final_response:
                    bot_message = GroupMessage(
                        conversation_id=request.conversation_id,
                        role="assistant",
                        content=final_response,
                        sender_name=bot.name
                    )
                    db.add(bot_message)
                    await db.commit()
                    
                    all_messages.append({
                        "role": "assistant",
                        "content": final_response,
                        "sender_name": bot.name,
                        "bot_id": bot.id
                    })
                else:
                    final_response = "抱歉，我遇到了一些问题。"
                    yield f"data: {json.dumps({'type': 'chunk', 'bot_name': bot.name, 'content': final_response})}\n\n"
                
                yield f"data: {json.dumps({'type': 'bot_done', 'bot_name': bot.name})}\n\n"
                
                await asyncio.sleep(0.5)
            
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            print(f"[ERROR] 流式消息失败: {str(e)}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/message", response_model=dict)
async def add_group_message(request: GroupChatMessageRequest, db: AsyncSession = Depends(get_db)):
    """在群聊中添加用户消息（非流式）"""
    
    # 获取所有机器人
    bots = []
    for bot_id in request.bot_ids:
        result = await db.execute(select(Bot).where(Bot.id == bot_id))
        bot = result.scalar_one_or_none()
        if bot:
            bots.append(bot)
    
    if not bots:
        raise HTTPException(status_code=400, detail="没有有效的机器人")
    
    try:
        result = await group_chat_service.add_user_message(
            db=db,
            conversation_id=request.conversation_id,
            user_name=request.user_name,
            user_prompt=request.message,
            bots=bots,
            include_docs=request.include_docs
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"消息发送失败: {str(e)}")


@router.get("/conversation/{conversation_id}", response_model=List[MessageResponse])
async def get_group_conversation_messages(conversation_id: int, db: AsyncSession = Depends(get_db)):
    """获取群聊消息"""
    result = await db.execute(
        select(GroupMessage).where(GroupMessage.conversation_id == conversation_id).order_by(GroupMessage.created_at)
    )
    messages = result.scalars().all()
    return messages


# ==================== 自动聊天 API ====================

from pydantic import BaseModel
from typing import Optional


class AutoChatRequest(BaseModel):
    conversation_id: int
    bot_ids: List[int]
    auto_rounds: int = 3  # 默认3轮


@router.post("/auto-chat")
async def start_auto_chat(request: AutoChatRequest, db: AsyncSession = Depends(get_db)):
    """
    启动机器人自动聊天
    机器人会自动回复多轮，用户可以随时停止
    """
    
    print(f"[DEBUG] 收到自动聊天请求: conversation_id={request.conversation_id}, rounds={request.auto_rounds}")
    
    # 获取会话锁
    loop_id = group_chat_service._acquire_lock(request.conversation_id)
    if not loop_id:
        raise HTTPException(status_code=409, detail="已有自动聊天正在进行中")
    
    async def event_generator():
        try:
            # 获取所有机器人
            bots = []
            for bot_id in request.bot_ids:
                result = await db.execute(select(Bot).where(Bot.id == bot_id))
                bot = result.scalar_one_or_none()
                if bot:
                    bots.append(bot)
            
            if not bots:
                yield f"data: {json.dumps({'error': '没有有效的机器人'})}\n\n"
                return
            
            # 获取历史消息
            result = await db.execute(
                select(GroupMessage).where(GroupMessage.conversation_id == request.conversation_id)
            )
            history_messages = result.scalars().all()
            
            all_messages = []
            for msg in history_messages:
                msg_dict = {
                    "role": msg.role,
                    "content": msg.content,
                    "sender_name": msg.sender_name or ""
                }
                if msg.role == "assistant":
                    msg_dict["bot_id"] = msg.bot_id
                all_messages.append(msg_dict)
            
            # 发送开始信号
            yield f"data: {json.dumps({'type': 'auto_start', 'conversation_id': request.conversation_id, 'rounds': request.auto_rounds})}\n\n"
            
            # 执行自动聊天
            async for event in auto_chat_rounds(
                service=group_chat_service,
                db=db,
                conversation_id=request.conversation_id,
                bots=bots,
                all_messages=all_messages,
                auto_rounds=request.auto_rounds,
                loop_id=loop_id
            ):
                # 将事件转换为 JSON 并发送
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            
            # 释放锁
            group_chat_service._release_lock(request.conversation_id, loop_id)
            
        except Exception as e:
            print(f"[ERROR] 自动聊天失败: {str(e)}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            # 释放锁
            group_chat_service._release_lock(request.conversation_id, loop_id)
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/stop-auto-chat")
async def stop_auto_chat(conversation_id: int = Query(..., description="会话ID")):
    """
    停止自动聊天
    """
    print(f"[DEBUG] 收到停止自动聊天请求: conversation_id={conversation_id}")
    
    # 释放锁即可停止自动聊天
    if conversation_id in group_chat_service._active_loops:
        del group_chat_service._active_loops[conversation_id]
        return {"status": "stopped", "conversation_id": conversation_id}
    else:
        return {"status": "not_running", "conversation_id": conversation_id}

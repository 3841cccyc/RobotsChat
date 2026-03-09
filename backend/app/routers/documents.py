from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import os
import shutil
from pathlib import Path
from app.database import get_db
from app.models import Bot, Document
from app.schemas import DocumentResponse
from app.services.rag_service import rag_service

router = APIRouter(prefix="/documents", tags=["documents"])

# 文档存储目录
UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/{bot_id}/upload", response_model=DocumentResponse)
async def upload_document(bot_id: int, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """上传文档到机器人"""
    
    # 检查机器人是否存在
    result = await db.execute(select(Bot).where(Bot.id == bot_id))
    bot = result.scalar_one_or_none()
    if not bot:
        raise HTTPException(status_code=404, detail="机器人不存在")
    
    # 获取文件类型
    file_ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
    file_type = file_ext if file_ext in ["pdf", "doc", "docx", "txt"] else "txt"
    
    # 保存文件
    file_path = os.path.join(UPLOAD_DIR, f"{bot_id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # 添加到向量库
        vector_store_id = await rag_service.add_document(bot_id, file_path, file_type)
        
        # 读取文件内容（用于存储）
        content = ""
        if file_type == "txt":
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        
        # 保存到数据库
        doc = Document(
            bot_id=bot_id,
            filename=file.filename,
            file_path=file_path,
            file_type=file_type,
            content=content[:10000],  # 限制存储的内容长度
            vector_store_id=vector_store_id
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
        
        return doc
    except Exception as e:
        # 清理上传的文件
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"文档处理失败: {str(e)}")


@router.get("/{bot_id}/list", response_model=List[DocumentResponse])
async def list_documents(bot_id: int, db: AsyncSession = Depends(get_db)):
    """获取机器人的文档列表"""
    result = await db.execute(
        select(Document).where(Document.bot_id == bot_id).order_by(Document.created_at.desc())
    )
    documents = result.scalars().all()
    return documents


@router.delete("/{document_id}")
async def delete_document(document_id: int, db: AsyncSession = Depends(get_db)):
    """删除文档"""
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 删除文件
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    
    await db.delete(doc)
    await db.commit()
    
    return {"message": "文档已删除"}

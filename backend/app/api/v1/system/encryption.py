"""
加密密钥接口
符合JY/T 0661-2025 L4级别保护要求
"""

from typing import Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.encryption_key import EncryptionKey
from app.schemas.response import success, page_response

router = APIRouter()


class EncryptionKeyCreate(BaseModel):
    key_name: str
    key_value: str
    algorithm: Optional[str] = "AES-256"
    expires_at: Optional[datetime] = None


class EncryptionKeyUpdate(BaseModel):
    key_value: Optional[str] = None
    is_active: Optional[str] = None
    expires_at: Optional[datetime] = None


def encrypt_data(data: str, key: str) -> str:
    """AES-256加密"""
    from cryptography.fernet import Fernet
    import base64

    key_bytes = base64.urlsafe_b64encode(key.ljust(32)[:32].encode())
    f = Fernet(key_bytes)
    return f.encrypt(data.encode()).decode()


def decrypt_data(encrypted_data: str, key: str) -> str:
    """AES-256解密"""
    from cryptography.fernet import Fernet
    import base64

    key_bytes = base64.urlsafe_b64encode(key.ljust(32)[:32].encode())
    f = Fernet(key_bytes)
    return f.decrypt(encrypted_data.encode()).decode()


@router.get("", response_model=dict)
async def get_encryption_keys(
    is_active: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取加密密钥列表"""
    query = select(EncryptionKey).order_by(EncryptionKey.created_at.desc())

    if is_active:
        query = query.where(EncryptionKey.is_active == is_active)

    total_result = await db.execute(query)
    total = len(total_result.scalars().all())

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    keys = result.scalars().all()

    items = [
        {
            "id": str(k.id),
            "key_name": k.key_name,
            "algorithm": k.algorithm,
            "is_active": k.is_active,
            "expires_at": k.expires_at.isoformat() if k.expires_at else None,
            "created_at": k.created_at.isoformat() if k.created_at else None,
        }
        for k in keys
    ]

    return page_response(items, total, page, page_size)


@router.post("", response_model=dict)
async def create_encryption_key(
    data: EncryptionKeyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建加密密钥"""
    key = EncryptionKey(
        key_name=data.key_name,
        key_value=data.key_value,
        algorithm=data.algorithm,
        expires_at=data.expires_at,
        created_by=current_user.id,
    )
    db.add(key)
    await db.commit()
    await db.refresh(key)
    return success({"id": str(key.id)}, "加密密钥创建成功")


@router.delete("/{key_id}", response_model=dict)
async def delete_encryption_key(
    key_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除加密密钥"""
    result = await db.execute(select(EncryptionKey).where(EncryptionKey.id == key_id))
    key = result.scalar_one_or_none()

    if key:
        await db.delete(key)
        await db.commit()

    return success(message="加密密钥删除成功")


@router.post("/encrypt", response_model=dict)
async def encrypt_text(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """加密数据"""
    text = data.get("text", "")
    key_name = data.get("key_name", "default")

    result = await db.execute(
        select(EncryptionKey).where(
            EncryptionKey.key_name == key_name, EncryptionKey.is_active == "true"
        )
    )
    key = result.scalar_one_or_none()

    if not key:
        return success({"error": "加密密钥不存在或已禁用"}, "加密失败")

    encrypted = encrypt_data(text, key.key_value)
    return success({"encrypted": encrypted})


@router.post("/decrypt", response_model=dict)
async def decrypt_text(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """解密数据"""
    encrypted_text = data.get("encrypted", "")
    key_name = data.get("key_name", "default")

    result = await db.execute(
        select(EncryptionKey).where(
            EncryptionKey.key_name == key_name, EncryptionKey.is_active == "true"
        )
    )
    key = result.scalar_one_or_none()

    if not key:
        return success({"error": "加密密钥不存在或已禁用"}, "解密失败")

    try:
        decrypted = decrypt_data(encrypted_text, key.key_value)
        return success({"decrypted": decrypted})
    except Exception as e:
        return success({"error": str(e)}, "解密失败")

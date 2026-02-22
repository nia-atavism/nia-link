"""
Neural-Bridge Authentication
API Key 認證模組
"""

from typing import Optional
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .config import get_settings

# Bearer Token 安全機制
security = HTTPBearer(
    scheme_name="API Key",
    description="Bearer Token 認證 - 使用 API Key 進行身份驗證"
)

# 可選的 Bearer Token（不會自動報錯）
optional_security = HTTPBearer(
    scheme_name="API Key",
    description="Bearer Token 認證 - 使用 API Key 進行身份驗證",
    auto_error=False
)


def get_valid_api_keys() -> set[str]:
    """獲取有效的 API Keys 集合"""
    settings = get_settings()
    return set(key.strip() for key in settings.api_keys.split(",") if key.strip())


async def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    驗證 API Key 的依賴注入函數
    
    Args:
        credentials: HTTP Authorization 標頭中的憑證
        
    Returns:
        str: 經過驗證的 API Key
        
    Raises:
        HTTPException: 當 API Key 無效或缺失時
    """
    api_key = credentials.credentials
    valid_keys = get_valid_api_keys()
    
    if api_key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": "error",
                "code": "UNAUTHORIZED",
                "message": "Invalid or missing API key"
            },
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return api_key


async def optional_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security)
) -> Optional[str]:
    """
    可選的 API Key 驗證（用於某些允許匿名訪問的端點）
    
    Returns:
        str | None: API Key 或 None
    """
    if credentials is None:
        return None
    
    api_key = credentials.credentials
    valid_keys = get_valid_api_keys()
    
    if api_key in valid_keys:
        return api_key
    
    return None


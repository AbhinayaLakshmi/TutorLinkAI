from fastapi import Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.exceptions import CredentialsException, RoleForbiddenException
from backend.app.database.session import get_db
from backend.app.models.user import User

reusable_oauth2 = HTTPBearer()

def get_current_user(
    token: HTTPAuthorizationCredentials = Security(reusable_oauth2),
    db: Session = Depends(get_db)
) -> User:
    try:
        payload = jwt.decode(
            token.credentials, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise CredentialsException()
    except JWTError:
        raise CredentialsException()
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise CredentialsException("User not found")
    
    return user

from typing import Union, List

def require_role(required_roles: Union[str, List[str]]):
    def role_dependency(current_user: User = Depends(get_current_user)) -> User:
        allowed = [required_roles.upper()] if isinstance(required_roles, str) else [r.upper() for r in required_roles]
        if current_user.role.upper() not in allowed:
            roles_str = required_roles if isinstance(required_roles, str) else ", ".join(required_roles)
            raise RoleForbiddenException(
                detail=f"Access denied: role {roles_str} required"
            )
        return current_user
    return role_dependency

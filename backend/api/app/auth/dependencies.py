from typing import Optional, List
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import User, Survey
from app.auth.security import decode_access_token

security_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    token = None
    if credentials:
        token = credentials.credentials
    elif authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token payload.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated.",
        )
    
    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    try:
        return await get_current_user(credentials, authorization, db)
    except HTTPException:
        return None


def require_role(allowed_roles: List[str]):
    """Decorator dependency to enforce Role-Based Access Control."""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role = current_user.role.upper()
        allowed = [r.upper() for r in allowed_roles]
        
        # ADMIN has universal access
        if user_role == "ADMIN" or user_role in allowed:
            return current_user
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: Requires one of roles {allowed_roles}. Current role: {current_user.role}",
        )
    return role_checker


def check_survey_access(survey_id: str, db: Session, user: User) -> Survey:
    """Validate survey existence and enforce survey-level authorization."""
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        # Also try matching by survey_code
        survey = db.query(Survey).filter(Survey.survey_code == survey_id).first()
        
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Survey '{survey_id}' was not found in the database.",
        )
    
    # ADMIN has universal access
    if user.role.upper() == "ADMIN":
        return survey
    
    # Creator always has access
    if survey.created_by == user.id:
        return survey
    
    # Completed surveys are accessible to verified organization engineers and viewers
    if survey.status == "COMPLETED" or user.role.upper() in ["ENGINEER", "VIEWER"]:
        return survey
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have authorization to access this private survey.",
    )

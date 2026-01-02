import os
from typing import Any, Dict, Optional
from datetime import timedelta, datetime, timezone
from uuid import UUID
import httpx
import jwt
from fastapi import Depends, HTTPException, requests, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from connections.postgres_connection import DBResourceManager, current_tenant_id
from config.env_loader import load_env
from google.oauth2 import id_token
from google.auth.transport.requests import Request as GoogleRequest

from custom_utilities.custom_exception import CustomException


load_env()
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URL = os.getenv("GOOGLE_REDIRECT_URL")
JWT_ISSUER = os.getenv("EDTECH_ISSUER")
JWT_AUDIENCE = os.getenv("EDTECH_AUDIENCE")
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 30
edtech_db_manager = DBResourceManager(db_key=os.getenv("POSTGRES_DB"))
security = HTTPBearer()
# GOOGLE_MOBILE_CLIENT_ID = os.getenv("GOOGLE_MOBILE_CLIENT_ID")

def validate_jwt_token_middleware(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Validates a JWT token from the Authorization header (Stateless).

    This function extracts the token, decodes it using the configured
    secret key and algorithm, and validates the token structure and claims.
    It does NOT check against any stored token in the database.

    Args:
        credentials (HTTPAuthorizationCredentials): HTTP bearer token obtained from the Authorization header.

    Returns:
        dict: The complete payload from the token including user_id, role_id, etc.

    Raises:
        HTTPException: If the token is missing, invalid, expired, or malformed.
    """
    token = credentials.credentials
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing access token.")

    try:
        payload = jwt.decode(
            token, 
            SECRET_KEY, 
            algorithms=[ALGORITHM], 
            audience=JWT_AUDIENCE, 
            issuer=JWT_ISSUER
        )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing user_id.")
        
        return payload

    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired."
        ) from exc
    
    except jwt.InvalidAudienceError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token audience."
        ) from exc
    
    except jwt.InvalidIssuerError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token issuer."
        ) from exc

    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token."
        ) from exc

def get_current_user(token_payload: dict = Depends(validate_jwt_token_middleware)) -> dict:
    """
    Extract current user information from validated JWT token and validate tenant context.
    
    Args:
        token_payload (dict): Validated JWT payload from middleware.
        
    Returns:
        dict: User information extracted from token.
    """
    # Validate that tenant context is set
    # tenant_id = current_tenant_id.get()
    # if not tenant_id:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Tenant context not set. Please provide X-Tenant header."
    #     )
    
    return {
        "user_id": token_payload.get("sub"),
        "role_id": token_payload.get("role_id"),
        "tenant_id": token_payload.get("tenant_id"),
        "issued_at": token_payload.get("iat"),
        "expires_at": token_payload.get("exp")
    }

def generate_access_token(data: dict, user_id: str, tenant_id: UUID, role_id: int = None,
                        expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a stateless JWT access token.

    Args:
        data (dict): Additional data to encode in the token.
        user_id (str): User ID for the token.
        role_id (int, optional): User's role ID.
        expires_delta (timedelta, optional): Expiration time for the token.

    Returns:
        str: Encoded JWT token.
    """
    try:
        # Get current time for iat (issued at)
        now = datetime.now(timezone.utc)
        
        # Calculate expiration time
        if expires_delta:
            expire = now + expires_delta
        else:
            expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        # Build the complete JWT payload
        to_encode = {
            "sub": str(user_id),  # Subject (user identifier)
            "iss": JWT_ISSUER,    # Issuer
            "aud": JWT_AUDIENCE,  # Audience
            "exp": expire,        # Expiration time
            "iat": now,           # Issued at time
            "user_id": str(user_id),  # User ID (duplicate of sub for compatibility)
            "tenant_id": str(tenant_id),
            "token_type": "access"
        }
        
        # Add role_id if provided
        if role_id is not None:
            to_encode["role_id"] = role_id
        elif "role_id" in data:
            to_encode["role_id"] = data["role_id"]
        
        # Add any additional data from the input (excluding reserved claims)
        reserved_claims = {"sub", "iss", "aud", "exp", "iat", "user_id", "tenant_id", "role_id"}
        for key, value in data.items():
            if key not in reserved_claims:
                to_encode[key] = value

        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        
        return encoded_jwt
        
    except jwt.PyJWTError as e:
        raise RuntimeError(f"Error occurred during JWT token encoding: {str(e)}") from e
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred: {str(e)}") from e
    
def generate_refresh_token(user_id: str, tenant_id: UUID, role_id: int = None) -> str:
    """
    Create a stateless JWT refresh token.
    """
    try:
        now = datetime.now(timezone.utc)
        expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode = {
            "sub": str(user_id),
            "iss": JWT_ISSUER,
            "aud": JWT_AUDIENCE,
            "exp": expire,
            "iat": now,
            "user_id": str(user_id),
            "tenant_id": str(tenant_id),
            "token_type": "refresh"  # Distinguish from access token
        }
        if role_id is not None:
            to_encode["role_id"] = role_id
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except jwt.PyJWTError as e:
        raise RuntimeError(f"Error occurred during refresh JWT token encoding: {str(e)}") from e
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred: {str(e)}") from e
    
@staticmethod
async def exchange_google_code(auth_code: str):
    """
    Exchanges the authorization code from Google for access and ID tokens.
    """
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": auth_code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URL,
        "grant_type": "authorization_code"
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=data)
    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to exchange code: {response.text}"
        )
    return response.json()

async def get_google_user_info(access_token):
    """
    Gets user info from Google using the access token.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Invalid access token")       
        return response.json()
    except Exception as e:
        raise e

def get_tenant_key_from_request(request: Request) -> str | None:
    return request.headers.get("X-Tenant")


def google_verify_token(id_token_str: str) -> Dict[str, Any]:
        """
        Verify Google ID token with Google servers.
        
        Returns: User info from Google if valid
        Raises: CustomException if invalid
        """
        # print("inside google verify func------------")
        # print("inside google verify func google mobile client id------------ ", GOOGLE_CLIENT_ID)
        
        try:
            # Verify token with Google
            idinfo = id_token.verify_oauth2_token(
                id_token_str, 
                GoogleRequest(),
                GOOGLE_CLIENT_ID
            )
            # print("after idinfo------------ ", idinfo)
            
            
            # Verify audience matches
            if idinfo['aud'] != GOOGLE_CLIENT_ID:
                raise CustomException("Invalid token audience", status_code=401)
            
            return {
                "email": idinfo.get("email"),
                "given_name": idinfo.get("given_name"),
                "family_name": idinfo.get("family_name"),
                "picture": idinfo.get("picture"),
                "email_verified": idinfo.get("email_verified", False)
            }
            
        except ValueError as e:
            raise CustomException("Invalid Google token", status_code=401) from e
        except Exception as e:
            raise CustomException("Token verification failed", status_code=500) from e




from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException
from passlib.context import CryptContext
from jose import JWTError, jwt

# 🔐 Secret config
SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"

# 🔑 Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 🔒 Token security
security = HTTPBearer()


# ✅ Get current user from token
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    user = verify_token(token)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid token ❌")

    return user 


# 🔐 Hash password
def hash_password(password: str):
    return pwd_context.hash(password)


# 🔍 Verify password
def verify_password(plain: str, hashed: str):
    return pwd_context.verify(plain, hashed)


# 🎟️ Create JWT token
def create_token(user_id: int):
    data = {"user_id": user_id}   # ✅ IMPORTANT
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


# 🔎 Verify JWT token
# def verify_token(token: str):
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

#         # ✅ FIX: normalize token structure
#         if "user_id" in payload:
#             return payload["user_id"]   # extract actual user

#         return payload

#     except JWTError as e:
#         print("TOKEN ERROR:", e)
#         return None
def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # ✅ Handle both formats safely
        if "user_id" in payload:
            return payload["user_id"]

        return payload

    except JWTError as e:
        print("TOKEN ERROR:", e)
        return None
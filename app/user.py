from fastapi import APIRouter, Depends, HTTPException
from app.auth import get_current_user, hash_password, verify_password, create_token

router = APIRouter()

# In-memory user storage
users = []


# ✅ Profile
@router.get("/profile")
def profile(user: dict = Depends(get_current_user)):
    return {
        "message": "Access granted ✅",
        "user": user
    }


# ✅ Register
@router.post("/register")
def register(username: str, password: str):
    for u in users:
        if u["username"] == username:
            raise HTTPException(status_code=400, detail="User already exists ❌")

    hashed = hash_password(password)

    user_id = len(users) + 1

    users.append({
        "id": user_id,
        "username": username,
        "password": hashed
    })

    return {"message": "User registered ✅"}


# ✅ Login
@router.post("/login")
def login(username: str, password: str):
    for u in users:
        if u["username"] == username:
            if verify_password(password, u["password"]):

                token = create_token({
                    "id": u["id"],
                    "username": u["username"]
                })

                return {
                    "message": "Login successful ✅",
                    "token": token
                }

    raise HTTPException(status_code=401, detail="Invalid credentials ❌")
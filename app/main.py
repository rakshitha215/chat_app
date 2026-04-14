from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from datetime import datetime
import json

from app.database import SessionLocal, Base, engine
from app.models import Message
from app.auth import get_current_user, verify_token
from app.user import router as user_router
from app.manager import ConnectionManager

# =========================
# Dummy group data
# =========================
groups = {
    1: [1, 2],  # Group 1 has user 1 and user 2
}

# =========================
# App initialization
# =========================
app = FastAPI()

# Create DB tables
Base.metadata.create_all(bind=engine)

# WebSocket manager
manager = ConnectionManager()

# Include routers
app.include_router(user_router)

# =========================
# DB Dependency
# =========================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =========================
# WebSocket Endpoint
# =========================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    await websocket.accept()

    user = verify_token(token)
    user_id = user["id"]

    await manager.connect(user_id, websocket)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            group_id = message["group_id"]
            content = message["content"]

            if group_id in groups:
                users = groups[group_id]

                for uid in users:
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "message",
                            "sender_id": user_id,
                            "group_id": group_id,
                            "content": content
                        }),
                        uid
                    )

    except WebSocketDisconnect:
        manager.disconnect(user_id)

# =========================
# APIs
# =========================

@app.get("/status/{user_id}")
def get_user_status(user_id: int):
    return manager.get_status(user_id)


@app.get("/")
def home():
    return {"message": "Chat backend is running 🚀"}


# =========================
# Send Private Message (REST)
# =========================
@app.post("/send")
def send_message(
    receiver_id: int,
    content: str,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user["id"] == receiver_id:
        return {"error": "Cannot send message to yourself ❌"}

    message = Message(
        sender_id=user["id"],
        receiver_id=receiver_id,
        content=content,
        timestamp=datetime.utcnow()
    )

    db.add(message)
    db.commit()

    return {"status": "Message sent ✅"}


# =========================
# Chat History API
# =========================
@app.get("/chat/{user_id}")
def get_chat(
    user_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    messages = db.query(Message).filter(
        ((Message.sender_id == user["id"]) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == user["id"]))
    ).all()

    return messages
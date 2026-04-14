from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import json

from app.database import SessionLocal, Base, engine
from app.models import Message
from app.auth import get_current_user, verify_token
from app.user import router as user_router

# =========================
# App init
# =========================
app = FastAPI()
Base.metadata.create_all(bind=engine)

# ✅ include user APIs (REGISTER / LOGIN)
app.include_router(user_router)

# =========================
# Dummy group data
# =========================
groups = {
    1: [1, 2],
}

# =========================
# DB dependency
# =========================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =========================
# Connection Manager
# =========================
class ConnectionManager:
    def __init__(self):
        self.active_connections = {}

    async def connect(self, user_id, websocket):
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id):
        self.active_connections.pop(user_id, None)

    async def send_personal_message(self, message, user_id):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(message)

manager = ConnectionManager()

# =========================
# WebSocket
# =========================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    await websocket.accept()

    user = verify_token(token)
    user_id = user["id"]

    await manager.connect(user_id, websocket)

    try:
        while True:
            data = json.loads(await websocket.receive_text())

            msg_type = data.get("type")
            content = data.get("content")

            # 🔹 GROUP CHAT
            if msg_type == "group":
                group_id = data.get("group_id")

                if group_id in groups:
                    for uid in groups[group_id]:
                        await manager.send_personal_message(
                            json.dumps({
                                "type": "group",
                                "sender_id": user_id,
                                "group_id": group_id,
                                "content": content
                            }),
                            uid
                        )

            # 🔹 PRIVATE CHAT
            elif msg_type == "private":
                receiver_id = data.get("receiver_id")

                # Save to DB
                db = SessionLocal()
                msg = Message(
                    sender_id=user_id,
                    receiver_id=receiver_id,
                    content=content,
                    timestamp=datetime.utcnow()
                )
                db.add(msg)
                db.commit()
                db.close()

                # send to receiver
                await manager.send_personal_message(
                    json.dumps({
                        "type": "private",
                        "sender_id": user_id,
                        "receiver_id": receiver_id,
                        "content": content
                    }),
                    receiver_id
                )

                # send to sender
                await manager.send_personal_message(
                    json.dumps({
                        "type": "private",
                        "sender_id": user_id,
                        "receiver_id": receiver_id,
                        "content": content
                    }),
                    user_id
                )

    except WebSocketDisconnect:
        manager.disconnect(user_id)

# =========================
# REST APIs (keep these)
# =========================

@app.post("/send")
def send_message(
    receiver_id: int,
    content: str,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    msg = Message(
        sender_id=user["id"],
        receiver_id=receiver_id,
        content=content,
        timestamp=datetime.utcnow()
    )
    db.add(msg)
    db.commit()

    return {"status": "Message saved ✅"}

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

@app.get("/")
def home():
    return {"message": "Chat backend is running 🚀"}
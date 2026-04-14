from datetime import datetime

class ConnectionManager:
    def __init__(self):
        self.active_connections = {}  # user_id -> websocket
        self.user_status = {}         # user_id -> "online/offline"
        self.last_seen = {}           # user_id -> timestamp

    async def connect(self, user_id: int, websocket):
        self.active_connections[user_id] = websocket
        self.user_status[user_id] = "online"

    def disconnect(self, user_id: int):
        self.active_connections.pop(user_id, None)
        self.user_status[user_id] = "offline"
        self.last_seen[user_id] = datetime.utcnow()

    async def send_personal_message(self, message: str, user_id: int):
        ws = self.active_connections.get(user_id)
        if ws:
            await ws.send_text(message)

    def get_status(self, user_id: int):
        return {
            "status": self.user_status.get(user_id, "offline"),
            "last_seen": self.last_seen.get(user_id)
        }
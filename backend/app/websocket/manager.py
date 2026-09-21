from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.active: dict[int, set[WebSocket]] = {}

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active.setdefault(user_id, set()).add(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        sockets = self.active.get(user_id)
        if sockets:
            sockets.discard(websocket)
            if not sockets:
                self.active.pop(user_id, None)

    async def broadcast_to_user(self, user_id: int, message: dict) -> None:
        sockets = self.active.get(user_id, set())
        for ws in list(sockets):
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(user_id, ws)


manager = ConnectionManager()
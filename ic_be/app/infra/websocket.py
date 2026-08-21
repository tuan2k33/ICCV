import json
from typing import Dict, Set

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.connections:
            self.connections[user_id] = set()
        self.connections[user_id].add(websocket)
        print(f"User {user_id} connected.")

    def disconnect(self, websocket: WebSocket):
        for user_id, websockets in list(self.connections.items()):
            if websocket in websockets:
                websockets.discard(websocket)
                if not websockets:
                    del self.connections[user_id]
                print(f"User {user_id} disconnected. Total connections: {self.count_all_connections()}")
                break

    async def send_to_user(self, user_id: str, message: dict):
        if user_id not in self.connections:
            return False

        websockets = self.connections[user_id]
        disconnected = set()

        for ws in websockets:
            try:
                await ws.send_text(json.dumps(message))
            except Exception as e:
                print(f"Send error to {user_id}: {e}")
                disconnected.add(ws)

        for ws in disconnected:
            self.disconnect(ws)

        return True

    async def broadcast(self, message: dict):
        print("Start broadcast Websocket")
        for user_id, websockets in list(self.connections.items()):
            for ws in set(websockets):
                try:
                    await ws.send_text(json.dumps(message))
                except Exception as e:
                    print(f"Broadcast error to {user_id}: {e}")
                    self.disconnect(ws)

    async def push_task_to_users(self, users: list, message: dict):
        for user_id in users:
            await self.send_to_user(user_id, message)

    def get_online_users(self):
        return list(self.connections.keys())

    def count_all_connections(self):
        return sum(len(ws_set) for ws_set in self.connections.values())


socket_manage = ConnectionManager()

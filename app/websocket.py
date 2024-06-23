import websockets
import asyncio
from fastapi import WebSocket

connections = {}

async def notify_project(project_id: int, message: str):
    if project_id in connections:
        for websocket in connections[project_id]:
            await websocket.send(message)

async def websocket_endpoint(websocket: WebSocket, project_id: int):
    await websocket.accept()
    if project_id not in connections:
        connections[project_id] = []
    connections[project_id].append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except Exception as e:
        connections[project_id].remove(websocket)
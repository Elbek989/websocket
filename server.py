import asyncio
import websockets

Users=set()
async def handler(websocket):
    Users.add(websocket)
    try:
        async for message in websocket:
            for user in Users:
                if user != websocket:
                    await user.send(message)
    finally:
        Users.remove(websocket)

async def main():
    async with websockets.serve(handler, "localhost", 8000):
        print("Server running")
        await asyncio.Future()
asyncio.run(main())

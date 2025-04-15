import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asyncio import sleep

class FrameBroadcastConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Extract roomId from URL route parameters
        self.room_id = self.scope['url_route']['kwargs']['roomId']
        # Create a unique group name per broadcast room
        self.group_name = f"broadcast_{self.room_id}"
        
        # Add this connection to the broadcast group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        # Accept the WebSocket connection
        await self.accept()

    async def disconnect(self, close_code):
        # Remove this connection from the group on disconnect
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # Parse the JSON message from the client
        data = json.loads(text_data)
        frame_data = data.get("frame")
        if frame_data:
            # Throttle: wait 200ms to simulate ~5 FPS broadcast.
            await sleep(0.2)
            # Broadcast the frame to everyone in the group
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "broadcast_frame",
                    "frame": frame_data,
                }
            )

    async def broadcast_frame(self, event):
        # Handler for messages sent to the group
        frame = event["frame"]
        # Send the frame data to WebSocket client
        await self.send(text_data=json.dumps({
            "frame": frame
        }))

# broadcast_app/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class FrameBroadcastConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Extract roomId from URL route parameters
        self.roomId = self.scope['url_route']['kwargs']['roomId']
        # Create a group name (e.g. "broadcast_room123")
        self.group_name = f"broadcast_{self.roomId}"
        
        # Add this connection to the group
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

    # Receive a message (frame data) from the broadcaster
    async def receive(self, text_data):
        data = json.loads(text_data)
        frame_data = data.get("frame")
        if frame_data:
            # Broadcast the frame to the group (i.e., all connected clients in this room)
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "broadcast_frame",
                    "frame": frame_data,
                }
            )

    # Handler for messages sent to the group
    async def broadcast_frame(self, event):
        frame = event["frame"]
        await self.send(text_data=json.dumps({
            "frame": frame
        }))

from channels.generic.websocket import AsyncWebsocketConsumer
import json

class SignalingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'signaling_{self.room_name}'
        print(f"WebSocket connection attempt: {self.scope['client']}")

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        message = json.loads(text_data)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'signaling_message',
                'message': message
            }
        )

    async def signaling_message(self, event):
        message = event['message']

        await self.send(text_data=json.dumps(message))
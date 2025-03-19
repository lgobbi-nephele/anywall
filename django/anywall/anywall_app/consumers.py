from channels.generic.websocket import AsyncWebsocketConsumer
import json

class SignalingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'signaling_{self.room_name}'

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

        

# old

# import json
# from channels.generic.websocket import AsyncWebsocketConsumer

# class SignalingConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         await self.channel_layer.group_add("signaling_group", self.channel_name)
#         await self.accept()

#     async def disconnect(self, close_code):
#         await self.channel_layer.group_discard("signaling_group", self.channel_name)

#     async def receive(self, text_data):
#         message = json.loads(text_data)
#         message_type = message.get('type')

#         # Invia il messaggio a tutti i client connessi
#         await self.channel_layer.group_send(
#             "signaling_group",
#             {
#                 'type': 'signaling_message',
#                 'message': message
#             }
#         )

#     async def signaling_message(self, event):
#         message = event['message']

#         # Invia il messaggio al WebSocket
#         await self.send(text_data=json.dumps(message))
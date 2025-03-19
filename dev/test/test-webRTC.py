import cv2
import numpy as np
import asyncio
import json
from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from aiortc.contrib.media import MediaBlackhole, MediaRecorder
import pyautogui
from av import VideoFrame

pcs = set()

class ScreenShareTrack(VideoStreamTrack):
    """
    A video track that captures the screen.
    """
    def __init__(self):
        super().__init__()

    async def recv(self):
        pts, time_base = await self.next_timestamp()

        # Capture the screen
        frame = pyautogui.screenshot()
        frame = cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR)

        # Convert to VideoFrame
        video_frame = VideoFrame.from_ndarray(frame, format="bgr24")
        video_frame.pts = pts
        video_frame.time_base = time_base
        return video_frame

async def index(request):
    content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebRTC Screen Share</title>
        <script>
            let pc = null;

            async function start() {
                pc = new RTCPeerConnection();

                pc.ontrack = function (event) {
                    document.getElementById('video').srcObject = event.streams[0];
                };

                // Add a transceiver for video with direction 'recvonly'
                pc.addTransceiver('video', { direction: 'recvonly' });

                const offer = await pc.createOffer();
                await pc.setLocalDescription(offer);

                const response = await fetch('/offer', {
                    method: 'POST',
                    body: JSON.stringify(pc.localDescription),
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                const answer = await response.json();
                await pc.setRemoteDescription(answer);
            }
        </script>

    </head>
    <body>
        <h1>WebRTC Screen Share</h1>
        <video id="video" autoplay playsinline></video>
        <button onclick="start()">Start Screen Share</button>
    </body>
    </html>
    """
    return web.Response(content_type="text/html", text=content)

async def offer(request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("iceconnectionstatechange")
    async def on_iceconnectionstatechange():
        if pc.iceConnectionState == "failed":
            await pc.close()
            pcs.discard(pc)

    # Set up the transceiver for screen sharing (video only)
    pc.addTransceiver("video", direction="sendonly")
    pc.addTrack(ScreenShareTrack())

    # Handle the offer
    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.Response(
        content_type="application/json",
        text=json.dumps({"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}),
    )

async def on_shutdown(app):
    # Close peer connections on shutdown
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()

if __name__ == "__main__":
    app = web.Application()
    app.on_shutdown.append(on_shutdown)
    app.router.add_get("/", index)
    app.router.add_post("/offer", offer)
    web.run_app(app, port=8080)

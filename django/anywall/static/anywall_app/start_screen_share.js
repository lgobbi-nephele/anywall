const startButton = document.getElementById("startScreenShare");
let peerConnection;
const config = {
  iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
};

let signalingSocket = null;
let stream = null;

startButton.addEventListener("click", async () => {
  try {
    // Close previous stream and peer connection if they exist
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      stream = null;
    }
    if (peerConnection) {
      peerConnection.close();
      peerConnection = null;
    }
    if (signalingSocket) {
      signalingSocket.close();
      signalingSocket = null;
    }

    const targetWindow = document.getElementById(
      "screenShareWindowIdOpen"
    ).value;
    console.log(`Target window: ${targetWindow}`);
    const roomName = "room_window_" + targetWindow; // Use a unique room name for each connection

    // Update the WebSocket URL to use the local IP address
    signalingSocket = new WebSocket(
      `ws://${SERVER_IP}:8000/ws/signaling/${roomName}/`
    );
    signalingSocket.onopen = async () => {
      console.log("WebSocket connection opened");

      // Check if getDisplayMedia is available
      if (navigator.mediaDevices && navigator.mediaDevices.getDisplayMedia) {
        stream = await navigator.mediaDevices.getDisplayMedia({
          video: true,
          audio: false,
        });
      } else {
        throw new Error("getDisplayMedia is not supported in this browser.");
      }

      peerConnection = new RTCPeerConnection(config);

      stream.getTracks().forEach((track) => {
        console.log(`Adding track: ${track.kind}`);
        peerConnection.addTrack(track, stream);
      });

      peerConnection.onicecandidate = (event) => {
        if (event.candidate) {
          console.log("Sending ICE candidate");
          signalingSocket.send(
            JSON.stringify({
              type: "candidate",
              candidate: event.candidate,
            })
          );
        }
      };

      peerConnection.onnegotiationneeded = async () => {
        console.log("Negotiation needed");
        const offer = await peerConnection.createOffer();
        await peerConnection.setLocalDescription(offer);
        signalingSocket.send(
          JSON.stringify({
            type: "offer",
            offer: peerConnection.localDescription,
          })
        );
      };

      peerConnection.ontrack = (event) => {
        console.log("Received remote track");
        const remoteVideo = document.getElementById("remoteVideo");
        remoteVideo.srcObject = event.streams[0];
      };

      peerConnection.onsetremotedescription = async () => {
        if (peerConnection.queuedCandidates) {
          for (const candidate of peerConnection.queuedCandidates) {
            await peerConnection.addIceCandidate(
              new RTCIceCandidate(candidate)
            );
          }
          peerConnection.queuedCandidates = [];
        }
      };

      peerConnection.onerror = (error) => {
        console.error("Peer connection error:", error);
      };

      peerConnection.oniceconnectionerror = () => {
        console.error("ICE connection failed");
      };
    };

    signalingSocket.onmessage = async (event) => {
      const message = JSON.parse(event.data);
      console.log(`Received message: ${message.type}`);
      if (message.type === "answer") {
        await peerConnection.setRemoteDescription(
          new RTCSessionDescription(message.answer)
        );
        console.log("Remote description set");
      } else if (message.type === "candidate") {
        if (peerConnection.remoteDescription) {
          await peerConnection.addIceCandidate(
            new RTCIceCandidate(message.candidate)
          );
        } else {
          peerConnection.queuedCandidates =
            peerConnection.queuedCandidates || [];
          peerConnection.queuedCandidates.push(message.candidate);
        }
      }
    };

    signalingSocket.onerror = (error) => {
      console.error("WebSocket error: ", error);
    };

    signalingSocket.onclose = () => {
      console.log("WebSocket connection closed");
    };
  } catch (err) {
    console.error("Error: " + err);
  }
});

window.addEventListener("beforeunload", () => {
  if (peerConnection) {
    peerConnection.close();
  }
  if (signalingSocket) {
    signalingSocket.close();
  }
});

window.addEventListener("unload", () => {
  if (peerConnection) {
    peerConnection.close();
  }
  if (signalingSocket) {
    signalingSocket.close();
  }
});

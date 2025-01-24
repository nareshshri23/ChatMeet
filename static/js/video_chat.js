// WebRTC configuration
const configuration = {
    iceServers: [
        { urls: 'stun:stun.l.google.com:19302' }
    ]
};

// Global variables
let localStream;
let peerConnections = {};
let localVideo;
let videoGrid;
let socket;

// DOM Elements
document.addEventListener('DOMContentLoaded', () => {
    localVideo = document.getElementById('localVideo');
    videoGrid = document.getElementById('videoGrid');
    
    // Control buttons
    const toggleVideoBtn = document.getElementById('toggleVideo');
    const toggleAudioBtn = document.getElementById('toggleAudio');
    const toggleChatBtn = document.getElementById('toggleChat');
    const leaveCallBtn = document.getElementById('leaveCall');
    
    // Chat elements
    const chatContainer = document.getElementById('chatContainer');
    const closeChat = document.getElementById('closeChat');
    const messageInput = document.getElementById('messageInput');
    const sendMessage = document.getElementById('sendMessage');
    
    // Initialize WebSocket connection
    initializeWebSocket();
    
    // Start local video
    initializeLocalVideo();
    
    // Event listeners for controls
    toggleVideoBtn.addEventListener('click', toggleVideo);
    toggleAudioBtn.addEventListener('click', toggleAudio);
    toggleChatBtn.addEventListener('click', () => {
        chatContainer.style.display = chatContainer.style.display === 'none' ? 'block' : 'none';
    });
    leaveCallBtn.addEventListener('click', leaveCall);
    closeChat.addEventListener('click', () => {
        chatContainer.style.display = 'none';
    });
    
    // Chat functionality
    sendMessage.addEventListener('click', sendChatMessage);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendChatMessage();
    });
});

// Initialize WebSocket connection
function initializeWebSocket() {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/ws/video/`;
    
    socket = new WebSocket(wsUrl);
    
    socket.onopen = () => {
        console.log('WebSocket connection established');
    };
    
    socket.onmessage = async (event) => {
        const data = JSON.parse(event.data);
        handleSocketMessage(data);
    };
    
    socket.onclose = () => {
        console.log('WebSocket connection closed');
    };
}

// Initialize local video
async function initializeLocalVideo() {
    try {
        localStream = await navigator.mediaDevices.getUserMedia({
            video: true,
            audio: true
        });
        localVideo.srcObject = localStream;
        broadcastNewUser();
    } catch (error) {
        console.error('Error accessing media devices:', error);
        alert('Unable to access camera and microphone');
    }
}

// Handle incoming WebSocket messages
async function handleSocketMessage(data) {
    switch (data.type) {
        case 'new-user':
            handleNewUser(data);
            break;
        case 'offer':
            handleOffer(data);
            break;
        case 'answer':
            handleAnswer(data);
            break;
        case 'ice-candidate':
            handleIceCandidate(data);
            break;
        case 'user-disconnected':
            handleUserDisconnected(data);
            break;
        case 'chat-message':
            handleChatMessage(data);
            break;
    }
}

// Create and handle peer connections
async function createPeerConnection(userId) {
    const peerConnection = new RTCPeerConnection(configuration);
    peerConnections[userId] = peerConnection;
    
    // Add local stream
    localStream.getTracks().forEach(track => {
        peerConnection.addTrack(track, localStream);
    });
    
    // Handle ICE candidates
    peerConnection.onicecandidate = (event) => {
        if (event.candidate) {
            socket.send(JSON.stringify({
                type: 'ice-candidate',
                candidate: event.candidate,
                target: userId
            }));
        }
    };
    
    // Handle incoming streams
    peerConnection.ontrack = (event) => {
        const remoteVideo = document.createElement('video');
        remoteVideo.srcObject = event.streams[0];
        remoteVideo.autoplay = true;
        remoteVideo.playsinline = true;
        
        const videoContainer = document.createElement('div');
        videoContainer.className = 'video-container';
        videoContainer.id = `video-${userId}`;
        videoContainer.appendChild(remoteVideo);
        
        const userInfo = document.createElement('div');
        userInfo.className = 'user-info';
        userInfo.innerHTML = `
            <span>${userId}</span>
            <span class="connection-status">🟢 Connected</span>
        `;
        videoContainer.appendChild(userInfo);
        
        videoGrid.appendChild(videoContainer);
    };
    
    return peerConnection;
}

// Control functions
function toggleVideo() {
    const videoTrack = localStream.getVideoTracks()[0];
    videoTrack.enabled = !videoTrack.enabled;
    document.getElementById('toggleVideo').classList.toggle('active');
}

function toggleAudio() {
    const audioTrack = localStream.getAudioTracks()[0];
    audioTrack.enabled = !audioTrack.enabled;
    document.getElementById('toggleAudio').classList.toggle('active');
}

function leaveCall() {
    // Stop all tracks
    localStream.getTracks().forEach(track => track.stop());
    
    // Close all peer connections
    Object.values(peerConnections).forEach(pc => pc.close());
    peerConnections = {};
    
    // Clear video grid
    while (videoGrid.firstChild) {
        videoGrid.removeChild(videoGrid.firstChild);
    }
    
    // Redirect to home
    window.location.href = '/';
}

// Chat functions
function sendChatMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();
    
    if (message) {
        socket.send(JSON.stringify({
            type: 'chat-message',
            message: message
        }));
        
        addMessageToChat('You', message, true);
        messageInput.value = '';
    }
}

function addMessageToChat(sender, message, isSent = false) {
    const chatMessages = document.getElementById('chatMessages');
    const messageElement = document.createElement('div');
    messageElement.className = `message ${isSent ? 'sent' : 'received'}`;
    messageElement.innerHTML = `
        <div class="message-content">
            <strong>${sender}:</strong> ${message}
        </div>
        <div class="message-time">${new Date().toLocaleTimeString()}</div>
    `;
    chatMessages.appendChild(messageElement);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Clean up on page unload
window.onbeforeunload = () => {
    leaveCall();
};

// Global variables
let socket;
let currentChatUser = null;
let usersList = [];

// DOM Elements
document.addEventListener('DOMContentLoaded', () => {
    // Initialize WebSocket connection
    initializeWebSocket();
    
    // Set up event listeners
    const messageInput = document.querySelector('.chat-input input');
    const sendButton = document.querySelector('.chat-input button');
    const fileButton = document.querySelector('.tool-button[title="Send File"]');
    const imageButton = document.querySelector('.tool-button[title="Send Image"]');
    const emojiButton = document.querySelector('.tool-button[title="Send Emoji"]');
    
    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
    
    fileButton.addEventListener('click', () => handleFileUpload('file'));
    imageButton.addEventListener('click', () => handleFileUpload('image'));
    emojiButton.addEventListener('click', toggleEmojiPicker);
    
    // Load online users
    loadOnlineUsers();
});

// Initialize WebSocket connection
function initializeWebSocket() {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/ws/chat/`;
    
    socket = new WebSocket(wsUrl);
    
    socket.onopen = () => {
        console.log('WebSocket connection established');
    };
    
    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleSocketMessage(data);
    };
    
    socket.onclose = () => {
        console.log('WebSocket connection closed');
        // Attempt to reconnect after a delay
        setTimeout(initializeWebSocket, 3000);
    };
}

// Handle incoming WebSocket messages
function handleSocketMessage(data) {
    switch (data.type) {
        case 'user_list':
            updateUsersList(data.users);
            break;
        case 'new_message':
            handleNewMessage(data);
            break;
        case 'user_status':
            updateUserStatus(data);
            break;
        case 'typing':
            handleTypingIndicator(data);
            break;
    }
}

// Load and display online users
function loadOnlineUsers() {
    const usersList = document.querySelector('.users-list');
    usersList.innerHTML = ''; // Clear existing list
    
    // Request user list from server
    socket.send(JSON.stringify({
        type: 'get_users'
    }));
}

// Update users list in UI
function updateUsersList(users) {
    const usersList = document.querySelector('.users-list');
    const userTemplate = document.getElementById('userTemplate');
    
    usersList.innerHTML = ''; // Clear existing list
    
    users.forEach(user => {
        const userCard = userTemplate.content.cloneNode(true);
        
        // Set user information
        userCard.querySelector('.user-name').textContent = user.name;
        userCard.querySelector('.user-emoji').textContent = user.emoji || '👤';
        userCard.querySelector('.user-preferences').textContent = user.preferences || '';
        
        // Add click handler
        const card = userCard.querySelector('.user-card');
        card.addEventListener('click', () => startChat(user));
        
        if (currentChatUser && currentChatUser.id === user.id) {
            card.classList.add('active');
        }
        
        usersList.appendChild(userCard);
    });
}

// Start chat with selected user
function startChat(user) {
    currentChatUser = user;
    
    // Update UI
    document.querySelector('.no-chat-selected').style.display = 'none';
    document.querySelector('.chat-messages').style.display = 'block';
    document.querySelector('.chat-input').style.display = 'block';
    
    // Mark user card as active
    document.querySelectorAll('.user-card').forEach(card => {
        card.classList.remove('active');
    });
    document.querySelector(`[data-user-id="${user.id}"]`)?.classList.add('active');
    
    // Load chat history
    loadChatHistory(user.id);
}

// Load chat history for selected user
function loadChatHistory(userId) {
    const chatMessages = document.querySelector('.chat-messages');
    chatMessages.innerHTML = ''; // Clear existing messages
    
    socket.send(JSON.stringify({
        type: 'get_chat_history',
        user_id: userId
    }));
}

// Send a message
function sendMessage() {
    if (!currentChatUser) return;
    
    const messageInput = document.querySelector('.chat-input input');
    const message = messageInput.value.trim();
    
    if (message) {
        socket.send(JSON.stringify({
            type: 'message',
            recipient: currentChatUser.id,
            content: message
        }));
        
        // Add message to UI
        addMessageToChat({
            sender: 'You',
            content: message,
            timestamp: new Date().toISOString(),
            sent: true
        });
        
        messageInput.value = '';
    }
}

// Add message to chat UI
function addMessageToChat(message) {
    const chatMessages = document.querySelector('.chat-messages');
    const messageTemplate = document.getElementById('messageTemplate');
    
    const messageElement = messageTemplate.content.cloneNode(true);
    const messageDiv = messageElement.querySelector('.message');
    
    messageDiv.classList.add(message.sent ? 'sent' : 'received');
    messageDiv.querySelector('.message-content').textContent = message.content;
    messageDiv.querySelector('.message-time').textContent = 
        new Date(message.timestamp).toLocaleTimeString();
    
    chatMessages.appendChild(messageElement);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Handle file uploads
function handleFileUpload(type) {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = type === 'image' ? 'image/*' : '*/*';
    
    input.onchange = (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        const reader = new FileReader();
        reader.onload = (e) => {
            socket.send(JSON.stringify({
                type: 'file',
                recipient: currentChatUser.id,
                file: {
                    name: file.name,
                    type: file.type,
                    data: e.target.result
                }
            }));
        };
        reader.readAsDataURL(file);
    };
    
    input.click();
}

// Toggle emoji picker
function toggleEmojiPicker() {
    // Implement emoji picker functionality
    // You can use a library like emoji-mart
}

// Handle typing indicator
let typingTimeout;
function handleTyping() {
    if (!currentChatUser) return;
    
    clearTimeout(typingTimeout);
    
    socket.send(JSON.stringify({
        type: 'typing',
        recipient: currentChatUser.id,
        typing: true
    }));
    
    typingTimeout = setTimeout(() => {
        socket.send(JSON.stringify({
            type: 'typing',
            recipient: currentChatUser.id,
            typing: false
        }));
    }, 1000);
}

// Update user status
function updateUserStatus(data) {
    const userCard = document.querySelector(`[data-user-id="${data.user_id}"]`);
    if (userCard) {
        const statusElement = userCard.querySelector('.user-status');
        statusElement.textContent = data.online ? 'Online' : 'Offline';
        statusElement.className = `user-status text-${data.online ? 'success' : 'secondary'}`;
    }
}

// Handle typing indicator
function handleTypingIndicator(data) {
    if (currentChatUser && data.user_id === currentChatUser.id) {
        const typingIndicator = document.querySelector('.typing-indicator');
        typingIndicator.style.display = data.typing ? 'block' : 'none';
    }
}

// Clean up on page unload
window.onbeforeunload = () => {
    socket.close();
};

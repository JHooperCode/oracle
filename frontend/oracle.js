const chatContainer = document.getElementById('chat-container');
const userInput = document.getElementById('user-input');

// Handle Enter key
userInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendMessage(userInput.value);
    }
});

window.UserAccess = {}
UserAccess.initialize_user = async function (userIdentifier) {
    try {
        const response = await fetch(`http://localhost:8000/initialize?user_identifier=${encodeURIComponent(userIdentifier)}`, {
            method: 'POST',
            mode: 'cors',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log(data);
        return data;
    } catch (error) {
        console.error('Error:', error);
        addMessageToChat('assistant', 'Sorry, there was an error processing your request.');
    }
}

addMessageToChat = function(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;
    messageDiv.textContent = content;
    chatContainer.appendChild(messageDiv);
    
    // Enhanced scrolling behavior
    messageDiv.scrollIntoView({ behavior: 'smooth', block: 'end' });
    // Fallback for older browsers
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

sendMessage = async function(entered_message) {
    const message = entered_message.trim();
    if (!message) return;

    // Add user message to chat
    addMessageToChat('user', message);
    userInput.value = '';

    try {
        const response = await fetch('http://localhost:8000/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        });

        const data = await response.json();
        
        // Add assistant's response to chat
        addMessageToChat('assistant', data.responses);
    } catch (error) {
        console.error('Error:', error);
        addMessageToChat('assistant', 'Sorry, there was an error processing your request.');
    }
}

clearChat = function() {
    const chatContainer = document.getElementById('chat-container');
    chatContainer.innerHTML = '';

}


refreshChat = async function() {
    clearChat(); // Use the clearChat function instead of direct DOM manipulation
    
    try {
        const response = await fetch('http://localhost:8000/get_conversation', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('Response data:', data);
        
        // Iterate through the messages and display them
        if (data.messages && Array.isArray(data.messages)) {
            data.messages.forEach(message => {
                // Map 'user' and 'assistant' roles to our display format
                const role = message.type === 'human' ? 'user' : 'assistant';
                addMessageToChat(role, message.content);
            });
        } else {
            console.error('Invalid message format:', data.messages);
        }
    } catch (error) {
        console.error('Error refreshing chat:', error);
        addMessageToChat('error', 'Sorry, there was an error refreshing the conversation.');
    }
}

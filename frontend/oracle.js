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

async function updateModelInfo() {
    try {
        console.log('Fetching model info...');
        const response = await fetch('http://localhost:8000/get_model_info', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        if (!response.ok) {
            const errorData = await response.json();
            console.error('Server error:', errorData);
            throw new Error(`HTTP error! status: ${response.status}, message: ${errorData.detail}`);
        }

        const data = await response.json();
        console.log('Received model info:', data);
        const modelInfoElement = document.getElementById('current-model-info');
        const elementId = modelInfoElement.id;
        if (modelInfoElement) {
            const modelInfo = document.createElement('h3');
            modelInfo.textContent = `${data.model_name} (${data.model_type})`;
            modelInfo.id = elementId;
            modelInfoElement.replaceWith(modelInfo);
        }
    } catch (error) {
        console.error('Error fetching model info:', error);
        const modelInfoElement = document.getElementById('current-model-info');
        if (modelInfoElement) {
            modelInfoElement.textContent = 'Model info unavailable';
        }
    }
}

// Update model info when page loads and periodically check until successful
document.addEventListener('DOMContentLoaded', async () => {
    // Try immediately
    await updateModelInfo();
    
    // If not successful, retry every 2 seconds for up to 30 seconds
    let attempts = 0;
    const maxAttempts = 15;
    const interval = setInterval(async () => {
        if (document.getElementById('current-model-info').textContent !== 'Model info unavailable' || attempts >= maxAttempts) {
            clearInterval(interval);
            return;
        }
        attempts++;
        await updateModelInfo();
    }, 2000);
});

// Update model info when user logs in
UserAccess.initialize_user = (function() {
    const original = UserAccess.initialize_user;
    return async function() {
        const result = await original.apply(this, arguments);
        // Wait a short moment for the backend to initialize after login
        setTimeout(async () => {
            await updateModelInfo();
        }, 1000);
        return result;
    };
})();

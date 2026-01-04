// DOM Elements
const talkToAgentBtn = document.getElementById('talk-to-agent');
const voiceModal = document.getElementById('voice-modal');
const closeModalBtn = document.getElementById('close-modal');
const startCallBtn = document.getElementById('start-call');
const connectionInfo = document.getElementById('connection-info');
const assistantStatus = document.getElementById('assistant-status');
const conversationArea = document.getElementById('conversation-area');
const countryCode = document.getElementById('country-code');
const avatarCircle = document.getElementById('avatar-circle');
const audioPlayer = document.getElementById('audio-player');
const phoneInput = document.getElementById('phone-number');
const questionInput = document.getElementById('question-input');
const sendQuestionBtn = document.getElementById('send-question');

// Configuration
const CONFIG = {
    BACKEND_URL: 'http://localhost:3001', // Backend server URL
    FONOSTER_NUMBER: '+16592468685', // Your Fonoster number (update this)
    CALL_TIMEOUT: 30000 // 30 seconds timeout
};

// State Management
let currentCall = null;
let isConnected = false;
let callTimer = null;

// Initialize Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    checkBackendConnection();
    initializeModal();
});

function initializeEventListeners() {
    // Modal Controls
    talkToAgentBtn.addEventListener('click', openVoiceModal);
    closeModalBtn.addEventListener('click', closeVoiceModal);
    voiceModal.addEventListener('click', handleModalBackdropClick);
    
    // Call Controls
    startCallBtn.addEventListener('click', initiateCall);
    
    // Text Input Controls
    sendQuestionBtn.addEventListener('click', sendQuestion);
    questionInput.addEventListener('keypress', handleQuestionKeypress);
    questionInput.addEventListener('input', handleQuestionInput);
    
    // Phone Input Controls
    phoneInput.addEventListener('input', validatePhoneInput);
    
    // Keyboard shortcuts
    document.addEventListener('keydown', handleKeyboardShortcuts);
}

function initializeModal() {
    // Initialize send button state
    sendQuestionBtn.disabled = true;
    
    // Add initial welcome message
    addMessageToConversation('assistant', 'Hi! I\'m your Sigmoix AI assistant. I can help you with product inquiries and information about our technology solutions. You can type your question below or request a phone call.');
}

// Modal Functions
function openVoiceModal() {
    voiceModal.classList.add('active');
    document.body.style.overflow = 'hidden';
    
    // Reset modal state
    resetModalState();
    
    // Add welcome animation
    setTimeout(() => {
        avatarCircle.style.animation = 'pulse 2s ease-in-out infinite';
    }, 300);
}

function closeVoiceModal() {
    voiceModal.classList.remove('active');
    document.body.style.overflow = '';
    
    // Clean up any active calls
    if (currentCall) {
        endCall();
    }
    
    hideAudioPlayer();
}

function handleModalBackdropClick(event) {
    if (event.target === voiceModal) {
        closeVoiceModal();
    }
}

function resetModalState() {
    connectionInfo.style.display = 'none';
    startCallBtn.textContent = 'Call Me';
    startCallBtn.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M20.01 15.38c-1.23 0-2.42-.2-3.53-.56-.35-.12-.74-.03-1.01.24l-1.57 1.97c-2.83-1.35-5.48-3.9-6.89-6.83l1.95-1.66c.27-.28.35-.67.24-1.02-.37-1.11-.56-2.3-.56-3.53 0-.54-.45-.99-.99-.99H4.19C3.65 3 3 3.24 3 3.99 3 13.28 10.73 21 20.01 21c.71 0 .99-.63.99-1.18v-3.45c0-.54-.45-.99-.99-.99z"/>
        </svg>
        Call Me
    `;
    startCallBtn.disabled = false;
    assistantStatus.textContent = 'Ready to help you find products';
    isConnected = false;
    
    // Reset text input
    questionInput.value = '';
    sendQuestionBtn.disabled = true;
}

// Text Input Functions
function handleQuestionKeypress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendQuestion();
    }
}

function handleQuestionInput() {
    const hasText = questionInput.value.trim().length > 0;
    sendQuestionBtn.disabled = !hasText;
}

async function sendQuestion() {
    const question = questionInput.value.trim();
    if (!question) return;

    // Add user message to conversation
    addMessageToConversation('user', question);
    
    // Clear input and disable button temporarily
    questionInput.value = '';
    sendQuestionBtn.disabled = true;
    
    // Show typing indicator
    const typingElement = addMessageToConversation('assistant', 'Thinking...', true);
    
    try {
        const response = await fetch(`${CONFIG.BACKEND_URL}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: question })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Remove typing indicator
        if (typingElement) {
            typingElement.remove();
        }
        
        // Add assistant response
        addMessageToConversation('assistant', data.response || 'I apologize, but I encountered an error processing your request. Please try again.');
        
    } catch (error) {
        console.error('Error sending question:', error);
        
        // Remove typing indicator
        if (typingElement) {
            typingElement.remove();
        }
        
        // Add error message - fall back to demo mode
        addMessageToConversation('assistant', 'I\'m currently running in demo mode. Here\'s what I can tell you about our products: We offer a wide range of technology solutions including laptops, desktops, gaming computers, and accessories. Feel free to ask about specific product categories or price ranges!');
    }
}

// Phone Input Functions
function validatePhoneInput() {
    const phoneNumber = phoneInput.value.trim();
    const isValid = phoneNumber.length >= 10 && /^\+?[\d\s\-\(\)]+$/.test(phoneNumber);
    startCallBtn.disabled = !isValid || isConnected;
}

// Call Functions
async function initiateCall() {
    try {
        const phoneNumber = phoneInput.value.trim();
        
        if (!phoneNumber) {
            alert('Please enter your phone number');
            return;
        }

        if (!isValidPhoneNumber(phoneNumber)) {
            alert('Please enter a valid phone number');
            return;
        }
        
        startCallBtn.disabled = true;
        startCallBtn.textContent = 'Connecting...';
        connectionInfo.style.display = 'block';
        assistantStatus.textContent = 'Initiating call...';
        
        // Format phone number with country code
        const selectedCountryCode = countryCode.value;
        const formattedPhoneNumber = formatPhoneNumberForCall(phoneNumber, selectedCountryCode);
        
        // Make API call to backend to initiate Fonoster call
        const response = await fetch(`${CONFIG.BACKEND_URL}/api/initiate-call`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                phoneNumber: formattedPhoneNumber
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            handleCallSuccess(result);
        } else {
            throw new Error(result.error || 'Failed to initiate call');
        }
        
    } catch (error) {
        console.error('Call initiation failed:', error);
        handleCallError(error.message);
    }
}

function formatPhoneNumberForCall(phoneNumber, countryCode) {
    // Clean phone number
    let cleanNumber = phoneNumber.replace(/\D/g, '');
    
    // Add country code if not present
    if (!phoneNumber.startsWith('+')) {
        if (countryCode === '+880' && !cleanNumber.startsWith('880')) {
            cleanNumber = '880' + cleanNumber;
        } else if (countryCode === '+1' && !cleanNumber.startsWith('1')) {
            cleanNumber = '1' + cleanNumber;
        } else if (countryCode === '+44' && !cleanNumber.startsWith('44')) {
            cleanNumber = '44' + cleanNumber;
        }
    }
    
    return '+' + cleanNumber;
}

function handleCallSuccess(result) {
    currentCall = result.callId;
    isConnected = true;
    
    startCallBtn.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
        </svg>
        Call Connected
    `;
    startCallBtn.style.background = 'linear-gradient(135deg, #28a745, #20c997)';
    
    assistantStatus.textContent = 'Call connected! You should receive a call shortly.';
    
    // Add connected message to conversation
    addMessageToConversation('assistant', 'Great! I\'ve initiated a call to your number. Please answer your phone to start talking with me!');
    
    // Show audio player
    showAudioPlayer();
    
    // Start call timer
    startCallTimer();
    
    // Add end call button
    setTimeout(() => {
        startCallBtn.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 9c-1.6 0-3.15.25-4.6.72v3.1c0 .39-.23.74-.56.9-.98.49-1.87 1.12-2.66 1.85-.18.18-.43.28-.7.28-.28 0-.53-.11-.71-.29L.29 13.08c-.18-.17-.29-.42-.29-.7 0-.28.11-.53.29-.71C3.34 8.78 7.46 7 12 7s8.66 1.78 11.71 4.67c.18.18.29.43.29.71 0 .28-.11.53-.29.7l-2.48 2.48c-.18.18-.43.29-.71.29-.27 0-.52-.1-.7-.28-.79-.73-1.68-1.36-2.66-1.85-.33-.16-.56-.51-.56-.9v-3.1C15.15 9.25 13.6 9 12 9z"/>
            </svg>
            End Call
        `;
        startCallBtn.style.background = 'linear-gradient(135deg, #dc3545, #c82333)';
        startCallBtn.onclick = endCall;
    }, 2000);
}

function handleCallError(errorMessage) {
    console.error('Call error:', errorMessage);
    
    assistantStatus.textContent = 'Connection failed. Please try again.';
    connectionInfo.style.display = 'none';
    
    resetModalState();
    
    // Show error message
    addMessageToConversation('assistant', `Sorry, I couldn't connect the call. Error: ${errorMessage}. Please check your backend server and try again.`);
}

function endCall() {
    if (currentCall) {
        // In a real implementation, you'd call your backend to end the call
        console.log('Ending call:', currentCall);
        currentCall = null;
    }
    
    isConnected = false;
    clearInterval(callTimer);
    hideAudioPlayer();
    resetModalState();
    
    addMessageToConversation('assistant', 'Call ended. Feel free to call again if you need more help finding products!');
}

// Audio Player Functions
function showAudioPlayer() {
    audioPlayer.style.display = 'flex';
    
    // Simulate audio time update
    let seconds = 0;
    const timeDisplay = audioPlayer.querySelector('.audio-time');
    
    callTimer = setInterval(() => {
        seconds++;
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        timeDisplay.textContent = `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
    }, 1000);
}

function hideAudioPlayer() {
    audioPlayer.style.display = 'none';
    if (callTimer) {
        clearInterval(callTimer);
        callTimer = null;
    }
}

function startCallTimer() {
    // Auto-end call after timeout for demo purposes
    setTimeout(() => {
        if (isConnected) {
            addMessageToConversation('assistant', 'Demo call timeout reached. In production, calls can continue indefinitely.');
        }
    }, CONFIG.CALL_TIMEOUT);
}

// Conversation Functions
function addMessageToConversation(sender, message, isTyping = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    if (isTyping) {
        messageDiv.classList.add('typing-message');
    }
    
    if (sender === 'assistant') {
        messageDiv.innerHTML = `
            <div class="message-avatar">🤖</div>
            <div class="message-content">
                <p>${message}</p>
            </div>
        `;
    } else {
        messageDiv.innerHTML = `
            <div class="message-content">
                <p>${message}</p>
            </div>
            <div class="message-avatar">👤</div>
        `;
    }
    
    conversationArea.appendChild(messageDiv);
    
    // Auto-scroll to bottom
    conversationArea.scrollTop = conversationArea.scrollHeight;
    
    // Add animation
    messageDiv.style.opacity = '0';
    messageDiv.style.transform = 'translateY(20px)';
    
    setTimeout(() => {
        messageDiv.style.transition = 'all 0.3s ease';
        messageDiv.style.opacity = '1';
        messageDiv.style.transform = 'translateY(0)';
    }, 100);
    
    return messageDiv;
}

// Backend Connection Check
async function checkBackendConnection() {
    try {
        const response = await fetch(`${CONFIG.BACKEND_URL}/api/health`);
        if (response.ok) {
            console.log('Backend connection successful');
        } else {
            console.warn('Backend server not responding');
        }
    } catch (error) {
        console.warn('Backend server not available:', error.message);
        console.log('Demo mode: Call functionality will be simulated');
    }
}

// Keyboard Shortcuts
function handleKeyboardShortcuts(event) {
    // Escape key to close modal
    if (event.key === 'Escape' && voiceModal.classList.contains('active')) {
        closeVoiceModal();
    }
    
    // Ctrl/Cmd + K to open voice modal
    if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
        event.preventDefault();
        if (!voiceModal.classList.contains('active')) {
            openVoiceModal();
        }
    }
}

// Demo Mode Functions (for when backend is not available)
function simulateCall() {
    console.log('Running in demo mode - simulating call');
    
    setTimeout(() => {
        handleCallSuccess({ callId: 'demo-call-' + Date.now() });
        
        // Add some demo conversation
        setTimeout(() => {
            addMessageToConversation('assistant', 'This is a demo mode. In the real application, you would be connected to our voice assistant via phone call.');
        }, 2000);
        
        setTimeout(() => {
            addMessageToConversation('assistant', 'You can ask me about products like "Show me gaming computers" or "I need a laptop under 50,000 Taka".');
        }, 4000);
        
    }, 1500);
}

// Utility Functions
function isValidPhoneNumber(phoneNumber) {
    // Remove all non-digit characters for validation
    const cleanNumber = phoneNumber.replace(/\D/g, '');
    
    // Check if it's a valid length (10-15 digits)
    if (cleanNumber.length < 10 || cleanNumber.length > 15) {
        return false;
    }
    
    // Basic phone number pattern
    const phonePattern = /^[\+]?[\d\s\-\(\)]{10,}$/;
    return phonePattern.test(phoneNumber);
}

function formatPhoneNumber(phoneNumber) {
    // Basic phone number formatting
    const cleaned = phoneNumber.replace(/\D/g, '');
    const match = cleaned.match(/^(\d{3})(\d{3})(\d{4})$/);
    
    if (match) {
        return `+1 (${match[1]}) ${match[2]}-${match[3]}`;
    }
    
    return phoneNumber;
}

// Export functions for testing (if needed)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        openVoiceModal,
        closeVoiceModal,
        initiateCall,
        endCall,
        addMessageToConversation
    };
}
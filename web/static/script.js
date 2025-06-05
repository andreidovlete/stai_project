// Scroll chat to bottom on page load
window.onload = () => {
    const chatBody = document.getElementById("chat-body");
    if (chatBody) {
        chatBody.scrollTop = chatBody.scrollHeight;
    }
};

// Text-to-speech
function speak(text) {
    if ('speechSynthesis' in window && text.trim()) {
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'en-US';
        window.speechSynthesis.cancel(); // Stop any ongoing speech
        window.speechSynthesis.speak(utterance);
    }
}

// Add a chat bubble to the chat body
function addChatBubble(text, sender = 'bot') {
    const chatBody = document.getElementById("chat-body");

    const wrapper = document.createElement("div");
    wrapper.className = "bubble-wrapper";

    const bubble = document.createElement("div");
    bubble.className = `bubble ${sender === 'user' ? 'user-bubble' : 'bot-bubble'}`;
    bubble.innerText = text;

    wrapper.appendChild(bubble);
    chatBody.appendChild(wrapper);
    chatBody.scrollTop = chatBody.scrollHeight;

    // Speak bot message
    if (sender === 'bot') speak(text);
}

// Simulate bot thinking delay
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("chat-form");
    if (form) {
        form.addEventListener("submit", (e) => {
            const input = form.querySelector("input[name='message']");
            if (input && input.value.trim()) {
                e.preventDefault();

                const userMessage = input.value.trim();
                addChatBubble(userMessage, 'user'); // Show user message

                const chatBody = document.getElementById("chat-body");

                // Add bot placeholder "typing..."
                const placeholderWrapper = document.createElement("div");
                placeholderWrapper.className = "bubble-wrapper";

                const placeholderBubble = document.createElement("div");
                placeholderBubble.className = "bubble bot-bubble";
                placeholderBubble.innerHTML = "<em>Typing...</em>";

                placeholderWrapper.appendChild(placeholderBubble);
                chatBody.appendChild(placeholderWrapper);
                chatBody.scrollTop = chatBody.scrollHeight;

                setTimeout(() => {
                    placeholderWrapper.remove();
                    form.submit(); // Let Flask handle the response
                }, 1500);
            }
        });
    }
});

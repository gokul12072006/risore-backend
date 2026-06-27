const chatContainer = document.getElementById('chatContainer');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');

let chatHistory = [];
let currentFile = null;
let currentSessionId = null;
const API_URL = "http://127.0.0.1:8000/api";

let currentUserToken = null;
let initialLoadComplete = false;
let currentAiMode = 'Default';

function toggleAiModeMenu() {
    const menu = document.getElementById('aiModeMenu');
    if (menu) menu.classList.toggle('show');
}

function selectAiMode(mode) {
    currentAiMode = mode;
    const options = document.querySelectorAll('.mode-option');
    options.forEach(opt => {
        if (opt.textContent.trim() === mode) {
            opt.classList.add('active');
        } else {
            opt.classList.remove('active');
        }
    });
    
    const btn = document.getElementById('aiModeBtn');
    if (btn) {
        if (mode !== 'Default') btn.classList.add('active-mode');
        else btn.classList.remove('active-mode');
    }
    
    const menu = document.getElementById('aiModeMenu');
    if (menu) menu.classList.remove('show');
}

document.addEventListener('click', (e) => {
    const menu = document.getElementById('aiModeMenu');
    const btn = document.getElementById('aiModeBtn');
    if (menu && btn && !menu.contains(e.target) && !btn.contains(e.target)) {
        menu.classList.remove('show');
    }
});

function getDeviceId() {
    let id = localStorage.getItem('risore_device_id');
    if (!id) {
        id = 'device_' + Math.random().toString(36).substr(2, 9) + Date.now();
        localStorage.setItem('risore_device_id', id);
    }
    return id;
}
const deviceId = getDeviceId();

// FIREBASE CONFIGURATION - Replace with your own config from Firebase Console
const firebaseConfig = {
  apiKey: "AIzaSyASy2jt1u8Q6y1yYcnEX8e3SflQPRAg8jU",
  authDomain: "resore-ai.firebaseapp.com",
  projectId: "resore-ai",
  storageBucket: "resore-ai.firebasestorage.app",
  messagingSenderId: "150033114085",
  appId: "1:150033114085:web:c7b2fac713e259bd74050c",
  measurementId: "G-4GG8HK5KXW"
};

try {
    if (firebaseConfig.apiKey !== "YOUR_API_KEY") {
        firebase.initializeApp(firebaseConfig);
        
        firebase.auth().onAuthStateChanged(async (user) => {
            if (user) {
                // User is signed in
                document.getElementById('logged-out-ui').style.display = 'none';
                document.getElementById('logged-in-ui').style.display = 'flex';
                document.getElementById('user-name-display').textContent = user.displayName || user.email;
                
                currentUserToken = await user.getIdToken();
                
                // Sync with backend
                await fetch(`${API_URL}/sync_user`, {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${currentUserToken}` }
                }).catch(console.error);
                
                fetchSessions();
            } else {
                // User is signed out
                document.getElementById('logged-out-ui').style.display = 'flex';
                document.getElementById('logged-in-ui').style.display = 'none';
                currentUserToken = null;
                fetchSessions();
            }
        });
    } else {
        console.warn("Firebase not configured. Please add keys to app.js.");
    }
} catch (error) {
    console.error("Firebase init error", error);
}

window.signInWithGoogle = () => {
    if (firebaseConfig.apiKey === "YOUR_API_KEY") return alert("Please configure Firebase in app.js first.");
    const provider = new firebase.auth.GoogleAuthProvider();
    firebase.auth().signInWithPopup(provider).catch(e => alert(e.message));
};

window.signInWithFacebook = () => {
    if (firebaseConfig.apiKey === "YOUR_API_KEY") return alert("Please configure Firebase in app.js first.");
    const provider = new firebase.auth.FacebookAuthProvider();
    firebase.auth().signInWithPopup(provider).catch(e => alert(e.message));
};

window.signOut = () => {
    if (firebase.apps && firebase.apps.length) firebase.auth().signOut();
};

function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        currentFile = file;
        document.getElementById('filePreviewName').textContent = file.name;
        document.getElementById('filePreviewContainer').style.display = 'flex';
    }
}

function clearFile() {
    currentFile = null;
    document.getElementById('fileInput').value = '';
    document.getElementById('filePreviewContainer').style.display = 'none';
}

function setInput(text) {
    userInput.value = text;
    sendMessage();
}

userInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
});

userInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

async function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;

    // Clear welcome message if it exists
    const welcomeMsg = document.querySelector('.welcome-message');
    if (welcomeMsg) welcomeMsg.remove();
    
    // Hide suggestion cards
    const suggestionCards = document.getElementById('suggestionCards');
    if (suggestionCards) suggestionCards.style.display = 'none';

    // Add user message
    appendMessage(text, 'user');
    userInput.value = '';
    userInput.style.height = 'auto';

    // Add loading indicator
    const loadingId = 'loading-' + Date.now();
    const loadingHtml = `<div class="message msg-ai" id="${loadingId}"><div class="loading-dots"><span></span><span></span><span></span></div>${isDeepResearchMode ? '<div style="font-size:12px; color:var(--text-secondary); margin-top:10px;"><i class="ri-radar-fill ri-spin"></i> Deep Research in progress (this may take a minute)...</div>' : ''}</div>`;
    chatContainer.insertAdjacentHTML('beforeend', loadingHtml);
    chatContainer.scrollTop = chatContainer.scrollHeight;

    try {
        let response;
        if (currentFile) {
            // Send with file
            const formData = new FormData();
            const selectedLang = document.getElementById('languageSelect') ? document.getElementById('languageSelect').value : "English";
            formData.append("message", text);
            formData.append("language", selectedLang);
            formData.append("is_private", isPrivateMode);
            formData.append("is_deep_research", isDeepResearchMode);
            formData.append("ai_mode", currentAiMode);
            if (currentSessionId) formData.append("session_id", currentSessionId);
            formData.append("file", currentFile);

            const headers = { 'X-Device-ID': deviceId };
            if (currentUserToken) headers['Authorization'] = `Bearer ${currentUserToken}`;
            response = await fetch(`${API_URL}/chat_with_file`, {
                method: 'POST',
                headers: headers,
                body: formData
            });
            clearFile(); // clear attachment after sending
        } else {
            // Send regular text
            const selectedLang = document.getElementById('languageSelect') ? document.getElementById('languageSelect').value : "English";
            const headers = { 'Content-Type': 'application/json', 'X-Device-ID': deviceId };
            if (currentUserToken) headers['Authorization'] = `Bearer ${currentUserToken}`;
            response = await fetch(`${API_URL}/chat`, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({ message: text, history: isPrivateMode ? [] : chatHistory, language: selectedLang, is_private: isPrivateMode, is_deep_research: isDeepResearchMode, session_id: currentSessionId, ai_mode: currentAiMode })
            });
        }

        const data = await response.json();
        document.getElementById(loadingId).remove();
        
        if (response.ok) {
            appendMessage(data.response, 'ai', text);
            // Update history only if not private
            if (!isPrivateMode) {
                chatHistory.push({role: 'user', content: text});
                chatHistory.push({role: 'assistant', content: data.response});
                if (data.session_id && currentSessionId !== data.session_id) {
                    currentSessionId = data.session_id;
                    fetchSessions();
                }
            }
        } else {
            appendMessage("⚠️ Error: " + data.detail, 'ai');
        }
    } catch (error) {
        document.getElementById(loadingId).remove();
        appendMessage("⚠️ Connection error. Is the server running?", 'ai');
    }
}

function appendMessage(text, sender, originalQuery = null) {
    const div = document.createElement('div');
    div.className = `message msg-${sender}`;
    
    if (sender === 'ai') {
        let infographicHtml = '';
        let hasInfographic = false;
        
        let websiteHtml = '';
        let hasWebsite = false;
        
        // Extract Infographic Tag
        const infoMatch = text.match(/<GENERATE_INFOGRAPHIC>([\s\S]*?)<\/GENERATE_INFOGRAPHIC>/);
        if (infoMatch) {
            hasInfographic = true;
            infographicHtml = infoMatch[1];
            text = text.replace(infoMatch[0], '<div class="infographic-placeholder"><i><i class="ri-loader-4-line ri-spin"></i> Generating high-resolution infographic...</i></div>');
        }

        // Extract Website Tag
        const webMatch = text.match(/<GENERATE_WEBSITE>([\s\S]*?)<\/GENERATE_WEBSITE>/);
        if (webMatch) {
            hasWebsite = true;
            const codeMatch = webMatch[1].match(/<CODE>([\s\S]*?)<\/CODE>/);
            if (codeMatch) {
                websiteHtml = codeMatch[1].trim();
            }
            text = text.replace(webMatch[0], ''); // Remove the tag from the text
        }

        div.innerHTML = marked.parse(text);
        
        // Render Website Sandbox
        if (hasWebsite && websiteHtml) {
            const sandboxWrapper = document.createElement('div');
            sandboxWrapper.className = 'sandbox-wrapper';
            
            const sandboxHeader = document.createElement('div');
            sandboxHeader.className = 'sandbox-header';
            sandboxHeader.innerHTML = `
                <div class="mac-buttons"><span></span><span></span><span></span></div>
                <div class="sandbox-title"><i class="ri-macbook-line"></i> Live Preview</div>
                <div class="sandbox-actions">
                    <button class="sandbox-action-btn" onclick="downloadSandboxPdf(this.closest('.sandbox-wrapper').querySelector('iframe'))" title="Download as PDF" aria-label="Download as PDF"><i class="ri-file-pdf-line"></i></button>
                    <button class="sandbox-fullscreen" onclick="this.parentElement.parentElement.querySelector('iframe').requestFullscreen()" title="Fullscreen" aria-label="Fullscreen"><i class="ri-fullscreen-line"></i></button>
                </div>
            `;
            
            const iframe = document.createElement('iframe');
            iframe.className = 'sandbox-iframe';
            iframe.srcdoc = websiteHtml;
            iframe.sandbox = "allow-scripts allow-modals allow-same-origin";
            
            sandboxWrapper.appendChild(sandboxHeader);
            sandboxWrapper.appendChild(iframe);
            div.appendChild(sandboxWrapper);
        }
        
        // Trigger render after DOM update
        if (hasInfographic) {
            setTimeout(() => renderInfographic(infographicHtml, div), 200);
        }
        
        // Add download buttons to any generated images
        const images = div.querySelectorAll('img');
        images.forEach(img => {
            const wrapper = document.createElement('div');
            wrapper.className = 'generated-image-wrapper';
            
            img.parentNode.insertBefore(wrapper, img);
            wrapper.appendChild(img);
            
            const downloadBtn = document.createElement('button');
            downloadBtn.innerHTML = '<i class="ri-download-2-line"></i>';
            downloadBtn.className = 'image-download-btn';
            downloadBtn.title = 'Download Image';
            downloadBtn.onclick = async (e) => {
                e.preventDefault();
                try {
                    const response = await fetch(img.src);
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.style.display = 'none';
                    a.href = url;
                    a.download = 'risore_generated_image.png';
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                } catch (err) {
                    // Fallback if fetch fails (e.g. CORS issues)
                    const a = document.createElement('a');
                    a.href = img.src;
                    a.target = '_blank';
                    a.download = 'risore_generated_image.png';
                    a.click();
                }
            };
            wrapper.appendChild(downloadBtn);
        });

        // Add feedback buttons for AI responses
        if (originalQuery) {
            const feedbackRow = document.createElement('div');
            feedbackRow.className = 'feedback-row';
            feedbackRow.innerHTML = `
                <button onclick="sendFeedback('${escapeHtml(originalQuery)}', '${escapeHtml(text)}', 1)"><i class="ri-thumb-up-line"></i></button>
                <button onclick="sendFeedback('${escapeHtml(originalQuery)}', '${escapeHtml(text)}', 0)"><i class="ri-thumb-down-line"></i></button>
            `;
            div.appendChild(feedbackRow);
        }
    } else {
        div.textContent = text;
    }

    chatContainer.appendChild(div);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

async function renderInfographic(tagContent, messageDiv) {
    try {
        const titleMatch = tagContent.match(/<TITLE>([\s\S]*?)<\/TITLE>/);
        const contentMatch = tagContent.match(/<CONTENT>([\s\S]*?)<\/CONTENT>/);
        
        if (titleMatch && contentMatch) {
            const title = titleMatch[1].trim();
            const content = contentMatch[1].trim();
            
            const renderer = document.getElementById('infographic-renderer');
            document.getElementById('info-title').textContent = title;
            document.getElementById('info-content').innerHTML = marked.parse(content);
            
            // Wait for DOM to paint the hidden renderer
            await new Promise(r => setTimeout(r, 500));
            
            const canvas = await html2canvas(renderer, {
                backgroundColor: '#0f0f11',
                scale: 2, // 2x resolution for crisp text
                useCORS: true,
                logging: false
            });
            
            const imgData = canvas.toDataURL('image/png');
            
            // Remove the placeholder
            const placeholder = messageDiv.querySelector('.infographic-placeholder');
            if (placeholder) placeholder.remove();
            
            const wrapper = document.createElement('div');
            wrapper.className = 'generated-image-wrapper';
            
            const img = document.createElement('img');
            img.src = imgData;
            wrapper.appendChild(img);
            
            const downloadBtn = document.createElement('button');
            downloadBtn.innerHTML = '<i class="ri-download-2-line"></i>';
            downloadBtn.className = 'image-download-btn';
            downloadBtn.title = 'Download Infographic';
            downloadBtn.onclick = () => {
                const a = document.createElement('a');
                a.href = imgData;
                a.download = `Risore_${title.replace(/[^a-z0-9]/gi, '_')}.png`;
                a.click();
            };
            wrapper.appendChild(downloadBtn);
            
            messageDiv.appendChild(wrapper);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    } catch (e) {
        console.error("Infographic generation failed:", e);
        const placeholder = messageDiv.querySelector('.infographic-placeholder');
        if (placeholder) placeholder.innerHTML = '⚠️ Failed to generate infographic image.';
    }
}

async function sendFeedback(query, responseText, rating) {
    try {
        const headers = { 'Content-Type': 'application/json', 'X-Device-ID': deviceId };
        if (currentUserToken) headers['Authorization'] = `Bearer ${currentUserToken}`;
        const res = await fetch(`${API_URL}/feedback`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({ user_query: query, ai_response: responseText, rating: rating })
        });
        if (res.ok) {
            alert('Feedback recorded. Thank you!');
        }
    } catch (error) {
        console.error("Feedback error", error);
    }
}

function escapeHtml(unsafe) {
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}

// Private Mode & T&C Logic
document.addEventListener('DOMContentLoaded', () => {
    if (!localStorage.getItem('risore_tnc_accepted')) {
        const modal = document.getElementById('tncModal');
        if (modal) modal.style.display = 'flex';
    }
    fetchTrends();
});

window.acceptTnc = () => {
    localStorage.setItem('risore_tnc_accepted', 'true');
    const modal = document.getElementById('tncModal');
    if (modal) modal.style.display = 'none';
};

let isPrivateMode = false;
let isDeepResearchMode = false;

window.toggleDeepResearchMode = () => {
    const toggle = document.getElementById('deepResearchToggle');
    isDeepResearchMode = toggle ? toggle.checked : false;
};

window.togglePrivateMode = () => {
    const toggle = document.getElementById('privateModeToggle');
    isPrivateMode = toggle ? toggle.checked : false;
    
    // Completely clear the chat screen
    Array.from(chatContainer.children).forEach(child => child.remove());
    
    if (isPrivateMode) {
        document.body.classList.add('private-mode');
        chatHistory = [];
        currentSessionId = null;
        chatContainer.innerHTML = `<div class="welcome-message"><div class="glow-orb-center"></div><h2 id="welcomeHeading">Private Mode Active</h2><p>History will not be saved. You may discuss mature topics safely.</p></div>`;
    } else {
        document.body.classList.remove('private-mode');
        // New fresh public start
        chatHistory = [];
        currentSessionId = null;
        chatContainer.innerHTML = `<div class="welcome-message"><div class="glow-orb-center"></div><h2 id="welcomeHeading">Good Evening.</h2><p>Can I help you with anything ?</p></div>`;
    }
    
    // Restore suggestion cards
    const suggestionCards = document.getElementById('suggestionCards');
    if (suggestionCards) suggestionCards.style.display = 'flex';
    
    // Deselect sidebar items
    document.querySelectorAll('.session-item').forEach(item => item.classList.remove('active'));
};

window.toggleSidebar = () => {
    document.getElementById('sidebar').classList.toggle('hidden');
};

window.startNewChat = () => {
    if (isPrivateMode) {
        const toggle = document.getElementById('privateModeToggle');
        if(toggle) toggle.checked = false;
        togglePrivateMode();
        return;
    }
    chatHistory = [];
    currentSessionId = null;
    Array.from(chatContainer.children).forEach(child => child.remove());
    chatContainer.innerHTML = `<div class="welcome-message"><div class="glow-orb-center"></div><h2 id="welcomeHeading">Good Evening.</h2><p>Can I help you with anything ?</p></div>`;
    
    // Restore suggestion cards
    const suggestionCards = document.getElementById('suggestionCards');
    if (suggestionCards) suggestionCards.style.display = 'flex';
    
    document.querySelectorAll('.session-item').forEach(item => item.classList.remove('active'));
};

async function fetchSessions() {
    try {
        const headers = { 'X-Device-ID': deviceId };
        if (currentUserToken) headers['Authorization'] = `Bearer ${currentUserToken}`;
        const response = await fetch(`${API_URL}/sessions`, { headers });
        if (response.ok) {
            const sessions = await response.json();
            const list = document.getElementById('chatHistoryList');
            if (list) {
                list.innerHTML = '';
                sessions.forEach(s => {
                    const div = document.createElement('div');
                    div.className = 'session-item';
                    if (s.id === currentSessionId) div.classList.add('active');
                    div.innerHTML = `<i class="ri-message-3-line"></i> ${escapeHtml(s.title)}`;
                    div.onclick = () => loadSession(s.id);
                    list.appendChild(div);
                });
            }
            
            // Auto-load most recent session on first load
            if (!initialLoadComplete && sessions.length > 0 && !isPrivateMode) {
                initialLoadComplete = true;
                loadSession(sessions[0].id);
            }
        }
    } catch (e) { console.error("Error fetching sessions", e); }
}

async function loadSession(sessionId) {
    if (isPrivateMode) {
        alert("Please disable Private Mode to view past sessions.");
        return;
    }
    
    try {
        const headers = { 'X-Device-ID': deviceId };
        if (currentUserToken) headers['Authorization'] = `Bearer ${currentUserToken}`;
        const response = await fetch(`${API_URL}/sessions/${sessionId}`, { headers });
        if (response.ok) {
            const messages = await response.json();
            currentSessionId = sessionId;
            chatHistory = messages.map(m => ({role: m.role, content: m.content}));
            
            // Render
            Array.from(chatContainer.children).forEach(child => child.remove());
            messages.forEach(m => {
                appendMessage(m.content, m.role === 'user' ? 'user' : 'ai');
            });
            
            fetchSessions(); // update active state
        }
    } catch (e) { console.error("Error loading session", e); }
}

async function fetchTrends() {
    try {
        const response = await fetch(`${API_URL}/trends`);
        if (response.ok) {
            const trends = await response.json();
            const container = document.getElementById('suggestionCards');
            if (container && trends.length > 0) {
                container.innerHTML = '';
                trends.forEach(trend => {
                    const card = document.createElement('div');
                    card.className = 'card';
                    card.onclick = () => setInput(trend.prompt);
                    card.innerHTML = `
                        <h3 title="${escapeHtml(trend.title)}"><i class="ri-flashlight-fill trend-icon"></i> ${escapeHtml(trend.title)}</h3>
                        <p>${escapeHtml(trend.description)}</p>
                    `;
                    container.appendChild(card);
                });
                startAutoScroll();
            }
        }
    } catch (e) {
        console.error("Failed to fetch trends", e);
        const container = document.getElementById('suggestionCards');
        if (container) container.innerHTML = '';
    }
}

let autoScrollInterval;
function startAutoScroll() {
    const container = document.getElementById('suggestionCards');
    if (!container) return;
    
    clearInterval(autoScrollInterval);
    autoScrollInterval = setInterval(() => {
        if (container.scrollLeft + container.clientWidth >= container.scrollWidth - 10) {
            container.scrollTo({left: 0, behavior: 'smooth'});
        } else {
            container.scrollBy({left: 295, behavior: 'smooth'});
        }
    }, 4000);
    
    container.onmouseenter = () => clearInterval(autoScrollInterval);
    container.onmouseleave = startAutoScroll;
}
// Utility for Sandbox PDF generation
window.downloadSandboxPdf = function(iframe) {
    const element = iframe.contentWindow.document.body;
    const opt = {
        margin:       0.5,
        filename:     'Risore_Resume.pdf',
        image:        { type: 'jpeg', quality: 0.98 },
        html2canvas:  { scale: 2, useCORS: true, windowWidth: 850 },
        jsPDF:        { unit: 'in', format: 'letter', orientation: 'portrait' }
    };
    // Notify user
    const originalBtn = event.currentTarget;
    originalBtn.innerHTML = '<i class="ri-loader-4-line ri-spin"></i>';
    
    html2pdf().set(opt).from(element).save().then(() => {
        originalBtn.innerHTML = '<i class="ri-file-pdf-line"></i>';
    });
};

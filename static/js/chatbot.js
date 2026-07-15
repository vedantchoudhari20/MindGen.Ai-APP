document.addEventListener("DOMContentLoaded", () => {
    // 1. Initialize Neural Network Background Mesh
    initBackgroundMesh();

    // 2. GSAP Entry Animations
    if (typeof gsap !== 'undefined') {
        // Fade in Navigation header
        gsap.from("header", { duration: 0.6, y: -40, opacity: 0, ease: "power2.out" });
        
        // Stagger list elements on Hero landing
        if (document.querySelector(".hero-content")) {
            gsap.from(".hero-badge", { duration: 0.6, y: 20, opacity: 0, ease: "power2.out", delay: 0.1 });
            gsap.from(".hero-title", { duration: 0.8, y: 20, opacity: 0, ease: "power2.out", delay: 0.2 });
            gsap.from(".hero-description", { duration: 0.8, y: 20, opacity: 0, ease: "power2.out", delay: 0.3 });
            gsap.from(".hero-actions", { duration: 0.6, y: 20, opacity: 0, ease: "power2.out", delay: 0.4 });
            gsap.from(".hero-visual", { duration: 0.8, scale: 0.9, opacity: 0, ease: "back.out(1.1)", delay: 0.3 });
        }

        // Stagger Dashboard components
        if (document.querySelector(".dashboard-grid")) {
            gsap.from(".welcome-text h2", { duration: 0.6, x: -30, opacity: 0, ease: "power2.out" });
            gsap.from(".welcome-text p", { duration: 0.6, x: -30, opacity: 0, ease: "power2.out", delay: 0.1 });
            gsap.from(".welcome-banner .btn", { duration: 0.6, scale: 0.8, opacity: 0, ease: "back.out(1.2)" });
            gsap.from(".feature-box", { duration: 0.6, y: 30, opacity: 0, stagger: 0.15, ease: "power2.out", delay: 0.2 });
            gsap.from(".glass-container.dashboard-card", { duration: 0.6, scale: 0.98, opacity: 0, ease: "power2.out" });
        }

        // Stagger Authentication Cards
        if (document.querySelector(".auth-card")) {
            gsap.from(".auth-card", { duration: 0.8, y: 40, opacity: 0, ease: "back.out(1.15)" });
        }

        // Results scale-in
        if (document.querySelector(".results-header")) {
            gsap.from(".results-header", { duration: 0.6, y: -20, opacity: 0, ease: "power2.out" });
            gsap.from(".result-card", { duration: 0.6, y: 30, opacity: 0, stagger: 0.12, ease: "power2.out", delay: 0.2 });
            gsap.from(".report-text-container", { duration: 0.8, y: 40, opacity: 0, ease: "power2.out", delay: 0.4 });
        }
    }

    // 2. Inject Chatbot Element to DOM
    injectChatbotWidget();
});

const KNOWLEDGE_BASE = {
    "genetics": "We analyze several key genetic variations (SNPs) associated with neurotransmitter pathways:<br>• <b>5-HTTLPR</b>: Affects serotonin transport and sensitivity to environmental stressors.<br>• <b>COMT</b>: Regulates dopamine levels in the prefrontal cortex.<br>• <b>MAOA</b>: Responsible for breaking down neurotransmitters like dopamine and serotonin.<br>• <b>MTHFR</b>: Governs folate conversion, vital for neurotransmitter synthesis.",
    "biomarkers": "Our biochemical panel evaluates:<br>• <b>Cortisol</b>: Evaluates HPA axis dysregulation and stress responses.<br>• <b>BDNF</b>: A key protein for neuroplasticity and brain cell growth.<br>• <b>GABA</b>: The primary inhibitory neurotransmitter that regulates calming responses.<br>• <b>Serotonin</b>: Essential for mood, sleep, and appetite regulation.<br>• <b>IL-6 & TNF-alpha</b>: Inflammatory markers related to neuroinflammation.",
    "system": "MindGen AI is a clinical assessment assistant. It aligns your lab chemistry results, genetic genotypes, and clinical scores (PHQ-9/GAD-7) to classify conditions into subtypes (e.g. Atypical Depression, Panic Disorder) and generate a multi-dimensional lifestyle, nutritional, and therapeutic pathway.",
    "pdf": "Once you complete an assessment, navigate to the <b>Results</b> page or open the <b>History</b> tab. Click the <b>Download PDF Report</b> button to save a clean, printable clinical summary of your care plan.",
    "hello": "Hello! How can I assist you with your genomic mental health insights today?",
    "hi": "Hi there! I am your MindGen AI Mentor. Let me know if you have questions about genetics or biomarkers.",
    "default": "That is an excellent question! MindGen AI focuses on integrating genetic variants (like COMT, 5-HTTLPR) with lab tests (Cortisol, Serotonin) and clinical scales (PHQ-9, GAD-7) to build personalized mental wellness recommendations. You can check your history or start a new assessment to see this in action."
};

function injectChatbotWidget() {
    const bubble = document.createElement('div');
    bubble.className = 'chatbot-bubble';
    bubble.id = 'chatBubble';
    bubble.innerHTML = `
        <svg viewBox="0 0 24 24">
            <path d="M12 3c-4.97 0-9 4.03-9 9 0 2.12.74 4.07 1.97 5.61L4.35 19.4c-.39.39-.39 1.02 0 1.41.39.39 1.02.39 1.41 0l1.9-1.9C9.04 19.64 10.48 20 12 20c4.97 0 9-4.03 9-9s-4.03-9-9-9zm0 15c-3.31 0-6-2.69-6-6s2.69-6 6-6 6 2.69 6 6-2.69 6-6 6zm-2-7c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1zm4 0c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1z"/>
        </svg>
    `;

    const windowEl = document.createElement('div');
    windowEl.className = 'chatbot-window';
    windowEl.id = 'chatWindow';
    windowEl.innerHTML = `
        <div class="chatbot-header">
            <h3>🧠 AI Mentor</h3>
            <button class="chatbot-close" id="closeChat">&times;</button>
        </div>
        <div class="chatbot-messages" id="chatMessages">
            <div class="chat-msg bot">Hello! I am your MindGen AI Mentor. Ask me anything about our genomic testing, biomarker analysis, or mental health recommendations!</div>
        </div>
        <div class="chatbot-suggestions">
            <button class="chat-suggest-btn" onclick="sendSuggestion('What genetic markers do you analyze?')">Genetics</button>
            <button class="chat-suggest-btn" onclick="sendSuggestion('What biomarkers are tested?')">Biomarkers</button>
            <button class="chat-suggest-btn" onclick="sendSuggestion('How does the recommendation system work?')">System Info</button>
        </div>
        <div class="chatbot-input-area">
            <input type="text" class="chatbot-input" id="chatInput" placeholder="Ask a question...">
            <button class="chatbot-send" id="sendChatBtn">
                <svg viewBox="0 0 24 24" style="width: 16px; height: 16px; fill: white;"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
            </button>
        </div>
    `;

    document.body.appendChild(bubble);
    document.body.appendChild(windowEl);

    // Click handler to toggle window
    bubble.addEventListener('click', () => {
        windowEl.classList.toggle('active');
        if (typeof gsap !== 'undefined' && windowEl.classList.contains('active')) {
            gsap.fromTo(windowEl, { scale: 0.9, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.3, ease: "back.out(1.1)" });
        }
    });

    document.getElementById('closeChat').addEventListener('click', () => {
        windowEl.classList.remove('active');
    });

    // Send button event
    const sendBtn = document.getElementById('sendChatBtn');
    const chatInput = document.getElementById('chatInput');
    
    sendBtn.addEventListener('click', handleUserMessage);
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            handleUserMessage();
        }
    });
}

function handleUserMessage() {
    const input = document.getElementById('chatInput');
    const text = input.value.trim();
    if (!text) return;

    appendMessage(text, 'user');
    input.value = '';

    // Simulate typing delay
    setTimeout(() => {
        const botResponse = getBotResponse(text);
        appendMessage(botResponse, 'bot');
    }, 600);
}

function sendSuggestion(question) {
    appendMessage(question, 'user');
    setTimeout(() => {
        const botResponse = getBotResponse(question);
        appendMessage(botResponse, 'bot');
    }, 600);
}

function appendMessage(text, sender) {
    const msgContainer = document.getElementById('chatMessages');
    const msg = document.createElement('div');
    msg.className = `chat-msg ${sender}`;
    msg.innerHTML = text;
    msgContainer.appendChild(msg);
    msgContainer.scrollTop = msgContainer.scrollHeight;
}

function getBotResponse(userMsg) {
    const text = userMsg.toLowerCase();
    if (text.includes("genetic") || text.includes("gene") || text.includes("dna") || text.includes("genotype")) {
        return KNOWLEDGE_BASE.genetics;
    } else if (text.includes("biomarker") || text.includes("cortisol") || text.includes("serotonin") || text.includes("gaba") || text.includes("bdnf") || text.includes("blood") || text.includes("lab")) {
        return KNOWLEDGE_BASE.biomarkers;
    } else if (text.includes("how") || text.includes("work") || text.includes("system") || text.includes("pipeline") || text.includes("algorithm")) {
        return KNOWLEDGE_BASE.system;
    } else if (text.includes("pdf") || text.includes("report") || text.includes("download") || text.includes("print")) {
        return KNOWLEDGE_BASE.pdf;
    } else if (text.includes("hello") || text.includes("hi ") || text.includes("hey")) {
        return KNOWLEDGE_BASE.hello;
    }
    return KNOWLEDGE_BASE.default;
}

function initBackgroundMesh() {
    const canvas = document.getElementById('bgCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    
    let width = canvas.width = window.innerWidth;
    let height = canvas.height = window.innerHeight;
    
    window.addEventListener('resize', () => {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
    });
    
    const particles = [];
    const maxParticles = Math.min(80, Math.floor((width * height) / 15000));
    
    class Particle {
        constructor() {
            this.x = Math.random() * width;
            this.y = Math.random() * height;
            this.vx = (Math.random() - 0.5) * 0.4;
            this.vy = (Math.random() - 0.5) * 0.4;
            this.radius = Math.random() * 2 + 1;
        }
        update() {
            this.x += this.vx;
            this.y += this.vy;
            
            if (this.x < 0 || this.x > width) this.vx *= -1;
            if (this.y < 0 || this.y > height) this.vy *= -1;
        }
        draw() {
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
            ctx.fillStyle = 'rgba(6, 182, 212, 0.4)';
            ctx.fill();
        }
    }
    
    for (let i = 0; i < maxParticles; i++) {
        particles.push(new Particle());
    }
    
    function animate() {
        ctx.clearRect(0, 0, width, height);
        
        // Draw connections
        for (let i = 0; i < particles.length; i++) {
            particles[i].update();
            particles[i].draw();
            
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                
                if (dist < 120) {
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.strokeStyle = `rgba(99, 102, 241, ${0.12 * (1 - dist / 120)})`;
                    ctx.lineWidth = 0.8;
                    ctx.stroke();
                }
            }
        }
        
        requestAnimationFrame(animate);
    }
    
    animate();
}

/**
 * Voice Control Module
 * Provides voice navigation and control using Web Speech API
 */

class VoiceControl {
    constructor() {
        this.recognition = null;
        this.isListening = false;
        this.isSupported = false;
        this.commandPalette = null;

        this.commands = {
            // Navigation commands
            "go to directory": () => this.navigate("businesses.html"),
            "go to businesses": () => this.navigate("businesses.html"),
            "go to map": () => this.navigate("map.html"),
            "go to trending": () => this.navigate("trending.html"),
            "go to deals": () => this.navigate("deals.html"),
            "go to saved": () => this.navigate("saved.html"),
            "go to friends": () => this.navigate("friends.html"),
            "go to reservations": () => this.navigate("reservations.html"),
            "go home": () => this.navigate("businesses.html"),
            "log out": () => this.logout(),
            "logout": () => this.logout(),

            // Scroll commands
            "scroll up": () => this.scroll("up"),
            "scroll down": () => this.scroll("down"),
            "go to top": () => this.scrollToTop(),
            "go to bottom": () => this.scrollToBottom(),

            // Search commands (prefix matching)
            "search": (query) => this.search(query),

            // Help
            "help": () => this.showHelp(),
            "show commands": () => this.showHelp(),

            // Click actions
            "click": (target) => this.clickElement(target),
            "press": (target) => this.clickElement(target),
        };

        this.init();
    }

    init() {
        // Check for browser support
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRecognition) {
            console.warn("Speech Recognition not supported in this browser.");
            return;
        }

        this.isSupported = true;
        this.recognition = new SpeechRecognition();
        this.recognition.continuous = false;
        this.recognition.interimResults = false;
        this.recognition.lang = "en-US";

        this.recognition.onstart = () => this.onStart();
        this.recognition.onend = () => this.onEnd();
        this.recognition.onresult = (event) => this.onResult(event);
        this.recognition.onerror = (event) => this.onError(event);

        this.createUI();
    }

    createUI() {
        // Create floating mic button
        const micBtn = document.createElement("button");
        micBtn.id = "voice-control-btn";
        micBtn.className = "voice-control-btn";
        micBtn.innerHTML = `<span class="mic-icon">MIC</span>`;
        micBtn.title = "Voice Control (Click to speak)";
        micBtn.setAttribute("aria-label", "Activate voice control");

        micBtn.addEventListener("click", () => this.toggle());

        document.body.appendChild(micBtn);

        // Create listening indicator
        const indicator = document.createElement("div");
        indicator.id = "voice-indicator";
        indicator.className = "voice-indicator hidden";
        indicator.innerHTML = `
            <div class="voice-indicator-content">
                <div class="pulse-ring"></div>
                <span class="listening-text">Listening...</span>
            </div>
        `;
        document.body.appendChild(indicator);

        // Create command palette
        this.createCommandPalette();
    }

    createCommandPalette() {
        const palette = document.createElement("div");
        palette.id = "command-palette";
        palette.className = "command-palette hidden";
        palette.innerHTML = `
            <div class="command-palette-content">
                <div class="command-palette-header">
                    <h3>Voice Commands</h3>
                    <button class="close-palette-btn">&times;</button>
                </div>
                <div class="command-palette-body">
                    <div class="command-section">
                        <h4>Navigation</h4>
                        <ul>
                            <li><code>"Go to directory"</code> - Open business directory</li>
                            <li><code>"Go to map"</code> - Open map view</li>
                            <li><code>"Go to trending"</code> - Open trending page</li>
                            <li><code>"Go to deals"</code> - Open deals page</li>
                            <li><code>"Go to saved"</code> - Open saved businesses</li>
                            <li><code>"Go to friends"</code> - Open friends page</li>
                            <li><code>"Go to reservations"</code> - Open reservations</li>
                            <li><code>"Log out"</code> - Sign out of account</li>
                        </ul>
                    </div>
                    <div class="command-section">
                        <h4>Scrolling</h4>
                        <ul>
                            <li><code>"Scroll up"</code> - Scroll page up</li>
                            <li><code>"Scroll down"</code> - Scroll page down</li>
                            <li><code>"Go to top"</code> - Scroll to page top</li>
                            <li><code>"Go to bottom"</code> - Scroll to page bottom</li>
                        </ul>
                    </div>
                    <div class="command-section">
                        <h4>Search</h4>
                        <ul>
                            <li><code>"Search [query]"</code> - Search for businesses</li>
                        </ul>
                    </div>
                    <div class="command-section">
                        <h4>Help</h4>
                        <ul>
                            <li><code>"Help"</code> - Show this command list</li>
                        </ul>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(palette);
        this.commandPalette = palette;

        // Close button
        palette.querySelector(".close-palette-btn").addEventListener("click", () => {
            this.hideCommandPalette();
        });

        // Close on outside click
        palette.addEventListener("click", (e) => {
            if (e.target === palette) {
                this.hideCommandPalette();
            }
        });
    }

    toggle() {
        if (!this.isSupported) {
            alert("Voice control is not supported in this browser. Please use Chrome or Edge.");
            return;
        }

        if (this.isListening) {
            this.stop();
        } else {
            this.start();
        }
    }

    start() {
        if (!this.isSupported || this.isListening) return;

        try {
            this.recognition.start();
        } catch (e) {
            console.error("Failed to start voice recognition:", e);
        }
    }

    stop() {
        if (!this.isSupported || !this.isListening) return;

        try {
            this.recognition.stop();
        } catch (e) {
            console.error("Failed to stop voice recognition:", e);
        }
    }

    onStart() {
        this.isListening = true;
        document.getElementById("voice-control-btn").classList.add("listening");
        document.getElementById("voice-indicator").classList.remove("hidden");
    }

    onEnd() {
        this.isListening = false;
        document.getElementById("voice-control-btn").classList.remove("listening");
        document.getElementById("voice-indicator").classList.add("hidden");
    }

    onResult(event) {
        const transcript = event.results[0][0].transcript.toLowerCase().trim();
        console.log("Voice command:", transcript);

        this.processCommand(transcript);
    }

    onError(event) {
        console.error("Voice recognition error:", event.error);
        this.onEnd();

        if (event.error === "no-speech") {
            // Silently handle no speech detected
        } else if (event.error === "not-allowed") {
            alert("Microphone access denied. Please allow microphone access to use voice control.");
        }
    }

    processCommand(transcript) {
        // Check for exact command matches
        for (const [command, action] of Object.entries(this.commands)) {
            if (transcript === command) {
                action();
                return;
            }
        }

        // Check for prefix commands (like "search ...")
        if (transcript.startsWith("search ")) {
            const query = transcript.substring(7).trim();
            this.search(query);
            return;
        }

        if (transcript.startsWith("click ") || transcript.startsWith("press ")) {
            const target = transcript.substring(6).trim();
            this.clickElement(target);
            return;
        }

        // No command matched
        this.showFeedback(`Command not recognized: "${transcript}". Say "help" for available commands.`);
    }

    // Command implementations
    navigate(page) {
        this.showFeedback(`Navigating to ${page.replace(".html", "")}...`);
        window.location.href = page;
    }

    logout() {
        const logoutBtn = document.getElementById("logout-btn");
        if (logoutBtn) {
            logoutBtn.click();
        }
    }

    scroll(direction) {
        const amount = direction === "up" ? -300 : 300;
        window.scrollBy({ top: amount, behavior: "smooth" });
    }

    scrollToTop() {
        window.scrollTo({ top: 0, behavior: "smooth" });
    }

    scrollToBottom() {
        window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
    }

    search(query) {
        if (!query) {
            this.showFeedback("Please specify what to search for.");
            return;
        }

        const searchInput = document.getElementById("search-input") ||
                           document.getElementById("map-search") ||
                           document.querySelector('input[type="search"]') ||
                           document.querySelector('input[placeholder*="Search"]');

        if (searchInput) {
            searchInput.value = query;
            searchInput.dispatchEvent(new Event("input", { bubbles: true }));

            // Try to trigger search button
            const searchBtn = document.getElementById("search-btn") ||
                             document.querySelector('button[type="submit"]');
            if (searchBtn) {
                searchBtn.click();
            } else {
                // Try Enter key
                searchInput.dispatchEvent(new KeyboardEvent("keypress", { key: "Enter", bubbles: true }));
            }

            this.showFeedback(`Searching for "${query}"...`);
        } else {
            this.showFeedback("No search field found on this page.");
        }
    }

    clickElement(target) {
        // Try to find element by text content
        const allElements = document.querySelectorAll("button, a, [role='button']");

        for (const el of allElements) {
            const text = el.textContent.toLowerCase().trim();
            if (text.includes(target)) {
                el.click();
                this.showFeedback(`Clicked "${el.textContent.trim()}"`);
                return;
            }
        }

        this.showFeedback(`Could not find element with text "${target}".`);
    }

    showHelp() {
        this.commandPalette.classList.remove("hidden");
    }

    hideCommandPalette() {
        this.commandPalette.classList.add("hidden");
    }

    showFeedback(message) {
        // Create or update feedback toast
        let toast = document.getElementById("voice-feedback");
        if (!toast) {
            toast = document.createElement("div");
            toast.id = "voice-feedback";
            toast.className = "voice-feedback";
            document.body.appendChild(toast);
        }

        toast.textContent = message;
        toast.classList.add("visible");

        setTimeout(() => {
            toast.classList.remove("visible");
        }, 3000);
    }
}

// Initialize voice control when DOM is ready
document.addEventListener("DOMContentLoaded", () => {
    window.voiceControl = new VoiceControl();
});

export default VoiceControl;

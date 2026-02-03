/**
 * Text-to-Speech Module
 * Provides read-aloud functionality using Web Speech Synthesis API
 */

class TextToSpeech {
    constructor() {
        this.synth = window.speechSynthesis;
        this.isSupported = !!this.synth;
        this.isPlaying = false;
        this.isPaused = false;
        this.currentUtterance = null;
        this.rate = 1.0;
        this.voices = [];

        if (this.isSupported) {
            this.init();
        }
    }

    init() {
        // Load voices
        this.loadVoices();

        // Voices may load asynchronously
        if (this.synth.onvoiceschanged !== undefined) {
            this.synth.onvoiceschanged = () => this.loadVoices();
        }

        this.createUI();
    }

    loadVoices() {
        this.voices = this.synth.getVoices();
        // Prefer English voices
        this.preferredVoice = this.voices.find(v =>
            v.lang.startsWith("en") && v.name.includes("Google")
        ) || this.voices.find(v => v.lang.startsWith("en")) || this.voices[0];
    }

    createUI() {
        // Create floating read-aloud button
        const readBtn = document.createElement("button");
        readBtn.id = "tts-btn";
        readBtn.className = "tts-btn";
        readBtn.innerHTML = `<span class="tts-icon">TTS</span>`;
        readBtn.title = "Read page aloud";
        readBtn.setAttribute("aria-label", "Read page content aloud");

        readBtn.addEventListener("click", () => this.toggleReadPage());

        document.body.appendChild(readBtn);

        // Create control bar
        const controlBar = document.createElement("div");
        controlBar.id = "tts-control-bar";
        controlBar.className = "tts-control-bar hidden";
        controlBar.innerHTML = `
            <div class="tts-controls">
                <button class="tts-ctrl-btn" id="tts-play-pause" title="Play/Pause">
                    <span class="play-icon">PLAY</span>
                    <span class="pause-icon hidden">PAUSE</span>
                </button>
                <button class="tts-ctrl-btn" id="tts-stop" title="Stop">STOP</button>
                <div class="tts-speed">
                    <label>Speed:</label>
                    <button class="speed-btn" data-speed="0.75">0.75x</button>
                    <button class="speed-btn active" data-speed="1">1x</button>
                    <button class="speed-btn" data-speed="1.25">1.25x</button>
                    <button class="speed-btn" data-speed="1.5">1.5x</button>
                </div>
                <button class="tts-ctrl-btn tts-close" id="tts-close" title="Close">&times;</button>
            </div>
            <div class="tts-progress">
                <div class="tts-progress-bar" id="tts-progress-bar"></div>
            </div>
        `;

        document.body.appendChild(controlBar);

        // Set up control bar events
        this.setupControlBarEvents(controlBar);
    }

    setupControlBarEvents(controlBar) {
        // Play/Pause
        controlBar.querySelector("#tts-play-pause").addEventListener("click", () => {
            if (this.isPaused) {
                this.resume();
            } else if (this.isPlaying) {
                this.pause();
            } else {
                this.readPage();
            }
        });

        // Stop
        controlBar.querySelector("#tts-stop").addEventListener("click", () => {
            this.stop();
        });

        // Close
        controlBar.querySelector("#tts-close").addEventListener("click", () => {
            this.stop();
            this.hideControlBar();
        });

        // Speed buttons
        controlBar.querySelectorAll(".speed-btn").forEach(btn => {
            btn.addEventListener("click", (e) => {
                controlBar.querySelectorAll(".speed-btn").forEach(b => b.classList.remove("active"));
                e.target.classList.add("active");
                this.rate = parseFloat(e.target.dataset.speed);

                // If currently playing, restart with new speed
                if (this.isPlaying) {
                    const text = this.currentText;
                    this.stop();
                    this.speak(text);
                }
            });
        });
    }

    toggleReadPage() {
        if (this.isPlaying) {
            this.stop();
            this.hideControlBar();
        } else {
            this.showControlBar();
            this.readPage();
        }
    }

    readPage() {
        // Get main content text
        const mainContent = document.querySelector(".main-content") ||
                           document.querySelector("main") ||
                           document.querySelector(".content-area") ||
                           document.body;

        // Extract readable text
        const text = this.extractReadableText(mainContent);

        if (!text.trim()) {
            this.showFeedback("No readable content found on this page.");
            return;
        }

        this.speak(text);
    }

    extractReadableText(element) {
        // Clone element to avoid modifying the DOM
        const clone = element.cloneNode(true);

        // Remove elements we don't want to read
        const removeSelectors = [
            "script", "style", "nav", "footer", "header",
            ".menu-bar", ".modal", ".hidden", "[aria-hidden='true']",
            "button", "input", "select", "textarea",
            ".tts-control-bar", ".voice-control-btn", ".tts-btn"
        ];

        removeSelectors.forEach(selector => {
            clone.querySelectorAll(selector).forEach(el => el.remove());
        });

        // Get text content
        let text = clone.textContent || clone.innerText || "";

        // Clean up text
        text = text
            .replace(/\s+/g, " ")
            .replace(/\n+/g, ". ")
            .trim();

        return text;
    }

    speak(text) {
        if (!this.isSupported) {
            alert("Text-to-Speech is not supported in this browser.");
            return;
        }

        this.stop();

        this.currentText = text;
        this.currentUtterance = new SpeechSynthesisUtterance(text);

        if (this.preferredVoice) {
            this.currentUtterance.voice = this.preferredVoice;
        }

        this.currentUtterance.rate = this.rate;
        this.currentUtterance.pitch = 1;
        this.currentUtterance.volume = 1;

        this.currentUtterance.onstart = () => this.onStart();
        this.currentUtterance.onend = () => this.onEnd();
        this.currentUtterance.onpause = () => this.onPause();
        this.currentUtterance.onresume = () => this.onResume();
        this.currentUtterance.onerror = (e) => this.onError(e);

        // Handle boundary events for progress
        this.currentUtterance.onboundary = (e) => this.onBoundary(e);

        this.synth.speak(this.currentUtterance);
    }

    pause() {
        if (this.isPlaying && !this.isPaused) {
            this.synth.pause();
        }
    }

    resume() {
        if (this.isPaused) {
            this.synth.resume();
        }
    }

    stop() {
        this.synth.cancel();
        this.isPlaying = false;
        this.isPaused = false;
        this.updatePlayPauseButton();
        this.resetProgress();
    }

    onStart() {
        this.isPlaying = true;
        this.isPaused = false;
        this.updatePlayPauseButton();
        document.getElementById("tts-btn").classList.add("playing");
    }

    onEnd() {
        this.isPlaying = false;
        this.isPaused = false;
        this.updatePlayPauseButton();
        document.getElementById("tts-btn").classList.remove("playing");
        this.resetProgress();
    }

    onPause() {
        this.isPaused = true;
        this.updatePlayPauseButton();
    }

    onResume() {
        this.isPaused = false;
        this.updatePlayPauseButton();
    }

    onError(event) {
        console.error("TTS Error:", event.error);
        this.onEnd();
    }

    onBoundary(event) {
        if (this.currentText && event.charIndex !== undefined) {
            const progress = (event.charIndex / this.currentText.length) * 100;
            this.updateProgress(progress);
        }
    }

    updatePlayPauseButton() {
        const playIcon = document.querySelector("#tts-play-pause .play-icon");
        const pauseIcon = document.querySelector("#tts-play-pause .pause-icon");

        if (this.isPlaying && !this.isPaused) {
            playIcon.classList.add("hidden");
            pauseIcon.classList.remove("hidden");
        } else {
            playIcon.classList.remove("hidden");
            pauseIcon.classList.add("hidden");
        }
    }

    updateProgress(percent) {
        const progressBar = document.getElementById("tts-progress-bar");
        if (progressBar) {
            progressBar.style.width = `${percent}%`;
        }
    }

    resetProgress() {
        this.updateProgress(0);
    }

    showControlBar() {
        document.getElementById("tts-control-bar").classList.remove("hidden");
    }

    hideControlBar() {
        document.getElementById("tts-control-bar").classList.add("hidden");
    }

    showFeedback(message) {
        // Reuse voice feedback toast if available, or create new
        let toast = document.getElementById("tts-feedback");
        if (!toast) {
            toast = document.createElement("div");
            toast.id = "tts-feedback";
            toast.className = "tts-feedback";
            document.body.appendChild(toast);
        }

        toast.textContent = message;
        toast.classList.add("visible");

        setTimeout(() => {
            toast.classList.remove("visible");
        }, 3000);
    }

    // Read a specific section or element
    readElement(element) {
        const text = this.extractReadableText(element);
        if (text.trim()) {
            this.showControlBar();
            this.speak(text);
        }
    }
}

// Initialize TTS when DOM is ready
document.addEventListener("DOMContentLoaded", () => {
    window.tts = new TextToSpeech();
});

export default TextToSpeech;

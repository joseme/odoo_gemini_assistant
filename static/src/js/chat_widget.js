/** @odoo-module **/

import { Component, useState, onMounted, useRef, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

class GeminiChatWidget extends Component {
    static template = "odoo_gemini_assistant.GeminiChatWidget";
    static props = {};

    setup() {
        super.setup();
        this.state = useState({
            isOpen: false,
            messages: [],
            inputText: "",
            isLoading: false,
            isRecording: false,
            isPlaying: false,
            config: null,
        });

        this.rpc = useService("rpc");
        this.notification = useService("notification");
        this.chatContainerRef = useRef("chatContainer");
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.currentAudio = null;

        onMounted(this.onMounted.bind(this));
        onWillUnmount(this.onWillUnmount.bind(this));
    }

    onMounted() {
        this.loadConfig();
    }

    onWillUnmount() {
        this.stopRecording();
    }

    async loadConfig() {
        try {
            const result = await this.rpc("/gemini_assistant/config", {});
            this.state.config = result;
        } catch (e) {
            console.error("Failed to load config:", e);
        }
    }

    toggleChat() {
        this.state.isOpen = !this.state.isOpen;
        if (this.state.isOpen) {
            setTimeout(() => this.scrollToBottom(), 100);
        }
    }

    getContext() {
        const action = odoo?.actionManager?.currentAction;
        const urlParams = new URLSearchParams(window.location.search);

        let module = null;
        let model = null;
        let resId = null;
        let viewType = null;

        if (action) {
            module = action.xmlid?.split(".")[0] || null;
            model = action.resModel || null;
            resId = action.resId || null;
            viewType = action.views?.[0]?.[1] || null;
        }

        const pathParts = window.location.pathname.split("/");
        if (pathParts.includes("web") && pathParts.includes("#")) {
            const hash = window.location.hash;
            if (hash.includes("model=")) {
                const modelMatch = hash.match(/model=([^&]+)/);
                if (modelMatch) model = modelMatch[1];
                const idMatch = hash.match(/id=(\d+)/);
                if (idMatch) resId = parseInt(idMatch[1]);
                const viewMatch = hash.match(/view_type=([^&]+)/);
                if (viewMatch) viewType = viewMatch[1];
            }
        }

        return { module, model, res_id: resId, view_type: viewType };
    }

    async sendMessage() {
        const text = this.state.inputText.trim();
        if (!text || this.state.isLoading) return;

        this.state.messages.push({ role: "user", content: text });
        this.state.inputText = "";
        this.state.isLoading = true;
        this.scrollToBottom();

        try {
            const context = this.getContext();
            const history = this.state.messages.map(m => ({
                role: m.role === "user" ? "user" : "assistant",
                content: m.content,
            }));

            const result = await this.rpc("/gemini_assistant/chat", {
                message: text,
                history: history,
                context: context,
            });

            if (result.error) {
                this.state.messages.push({
                    role: "assistant",
                    content: `Error: ${result.error}`,
                });
            } else {
                this.state.messages.push({
                    role: "assistant",
                    content: result.response,
                });
            }
        } catch (e) {
            this.state.messages.push({
                role: "assistant",
                content: "Error de conexión. Inténtalo de nuevo.",
            });
        }

        this.state.isLoading = false;
        this.scrollToBottom();
    }

    handleKeyPress(ev) {
        if (ev.key === "Enter" && !ev.shiftKey) {
            ev.preventDefault();
            this.sendMessage();
        }
    }

    async startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
            this.audioChunks = [];

            this.mediaRecorder.ondataavailable = (event) => {
                this.audioChunks.push(event.data);
            };

            this.mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(this.audioChunks, { type: "audio/webm" });
                await this.transcribeAudio(audioBlob);
                stream.getTracks().forEach(track => track.stop());
            };

            this.mediaRecorder.start();
            this.state.isRecording = true;
        } catch (e) {
            this.notification.add("No se pudo acceder al micrófono", { type: "danger" });
            console.error("Recording error:", e);
        }
    }

    stopRecording() {
        if (this.mediaRecorder && this.state.isRecording) {
            this.mediaRecorder.stop();
            this.state.isRecording = false;
        }
    }

    async transcribeAudio(audioBlob) {
        this.state.isLoading = true;

        try {
            const arrayBuffer = await audioBlob.arrayBuffer();
            const base64Audio = btoa(
                new Uint8Array(arrayBuffer).reduce(
                    (data, byte) => data + String.fromCharCode(byte),
                    ""
                )
            );

            const result = await this.rpc("/gemini_assistant/stt", {
                audio_data: base64Audio,
                sample_rate: 16000,
            });

            if (result.error) {
                this.notification.add(`Error de transcripción: ${result.error}`, { type: "danger" });
            } else if (result.text) {
                this.state.inputText = result.text;
                await this.sendMessage();
            }
        } catch (e) {
            this.notification.add("Error al transcribir audio", { type: "danger" });
            console.error("Transcription error:", e);
        }

        this.state.isLoading = false;
    }

    async playResponse(message) {
        if (this.state.isPlaying) {
            this.stopAudio();
            return;
        }

        this.state.isPlaying = true;

        try {
            const response = await fetch("/gemini_assistant/tts", {
                method: "POST",
                headers: { "Content-Type": "application/x-www-form-urlencoded" },
                body: `text=${encodeURIComponent(message.content)}`,
            });

            if (!response.ok) {
                throw new Error("TTS request failed");
            }

            const audioBlob = await response.blob();
            const audioUrl = URL.createObjectURL(audioBlob);

            this.currentAudio = new Audio(audioUrl);
            this.currentAudio.onended = () => {
                this.state.isPlaying = false;
                URL.revokeObjectURL(audioUrl);
            };
            this.currentAudio.onerror = () => {
                this.state.isPlaying = false;
                URL.revokeObjectURL(audioUrl);
            };

            await this.currentAudio.play();
        } catch (e) {
            this.state.isPlaying = false;
            console.error("TTS playback error:", e);
        }
    }

    stopAudio() {
        if (this.currentAudio) {
            this.currentAudio.pause();
            this.currentAudio.currentTime = 0;
            this.state.isPlaying = false;
        }
    }

    scrollToBottom() {
        if (this.chatContainerRef.el) {
            this.chatContainerRef.el.scrollTop = this.chatContainerRef.el.scrollHeight;
        }
    }

    formatMessage(text) {
        return text
            .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
            .replace(/\*(.*?)\*/g, "<em>$1</em>")
            .replace(/`(.*?)`/g, "<code>$1</code>")
            .replace(/\n/g, "<br>");
    }
}

registry.category("main_components").add("GeminiChatWidget", { Component: GeminiChatWidget });

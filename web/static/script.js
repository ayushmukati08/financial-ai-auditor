/**
 * Financial AI Auditor - Frontend Interaction Script
 */

document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const sidebar = document.getElementById("sidebar");
    const collapseBtn = document.getElementById("collapse-btn");
    const newChatBtn = document.getElementById("new-chat-btn");
    const chatSearchInput = document.getElementById("chat-search-input");
    const chatHistoryContainer = document.getElementById("chat-history");
    const documentsList = document.getElementById("documents-list");
    const chatContainer = document.getElementById("chat-container");
    const welcomeMessage = document.getElementById("welcome-message");
    const messagesList = document.getElementById("messages-list");
    const userInput = document.getElementById("user-input");
    const sendBtn = document.getElementById("send-btn");
    const fileUpload = document.getElementById("file-upload");
    const uploadedFilesContainer = document.getElementById("uploaded-files");
    const systemStatusText = document.getElementById("system-status-text");

    // Modal Elements
    const evidenceModal = document.getElementById("evidence-modal");
    const closeModalBtn = document.getElementById("close-modal-btn");
    const modalCitationTitle = document.getElementById("modal-citation-title");
    const modalCitationMeta = document.getElementById("modal-citation-meta");
    const modalCitationBody = document.getElementById("modal-citation-body");

    // State
    let currentEvidenceStore = {}; // Keyed by citation_id or id
    let chatSessions = JSON.parse(localStorage.getItem("audit_chat_sessions") || "[]");
    let currentSessionId = null;

    // --- 1. Load System Status & Documents ---
    async function fetchSystemHealth() {
        try {
            const res = await fetch("/api/health");
            if (res.ok) {
                const data = await res.json();
                systemStatusText.textContent = `Online (${data.vectors_count} vectors)`;
            }
        } catch (e) {
            systemStatusText.textContent = "Offline";
        }
    }

    async function fetchDocuments() {
        try {
            const res = await fetch("/api/documents");
            if (res.ok) {
                const data = await res.json();
                renderDocumentsList(data.documents || []);
            }
        } catch (e) {
            console.error("Failed to fetch documents", e);
        }
    }

    function renderDocumentsList(docs) {
        documentsList.innerHTML = "";
        if (docs.length === 0) {
            documentsList.innerHTML = '<div style="font-size: 12px; color: #777; padding-left: 6px;">No filings loaded</div>';
            return;
        }
        docs.forEach(doc => {
            const item = document.createElement("div");
            item.className = "document-item";
            item.innerHTML = `
                <span class="doc-icon">📄</span>
                <span class="doc-name" title="${doc.name}">${doc.name}</span>
                <span style="font-size: 10px; color: #888;">(${doc.chunks} ch)</span>
            `;
            documentsList.appendChild(item);
        });
    }

    // --- 2. Sidebar Toggles & Search ---
    collapseBtn.addEventListener("click", () => {
        sidebar.classList.toggle("collapsed");
    });

    chatSearchInput.addEventListener("input", (e) => {
        const query = e.target.value.toLowerCase();
        const items = chatHistoryContainer.querySelectorAll(".chat-item");
        items.forEach(item => {
            const text = item.textContent.toLowerCase();
            item.style.display = text.includes(query) ? "block" : "none";
        });
    });

    // --- 3. Chat Session Management ---
    function initNewChat() {
        currentSessionId = "session_" + Date.now();
        messagesList.innerHTML = "";
        welcomeMessage.style.display = "block";
        currentEvidenceStore = {};
        userInput.value = "";
        userInput.focus();
    }

    newChatBtn.addEventListener("click", initNewChat);

    function addChatToHistory(firstQuery) {
        const existing = chatSessions.find(s => s.id === currentSessionId);
        if (!existing) {
            chatSessions.unshift({
                id: currentSessionId,
                title: firstQuery.slice(0, 32) + (firstQuery.length > 32 ? "..." : ""),
                timestamp: Date.now()
            });
            localStorage.setItem("audit_chat_sessions", JSON.stringify(chatSessions.slice(0, 15)));
            renderChatHistory();
        }
    }

    function renderChatHistory() {
        chatHistoryContainer.innerHTML = "";
        chatSessions.forEach(session => {
            const item = document.createElement("div");
            item.className = "chat-item" + (session.id === currentSessionId ? " active" : "");
            item.textContent = "💬 " + session.title;
            item.addEventListener("click", () => {
                // Select chat
                currentSessionId = session.id;
                renderChatHistory();
            });
            chatHistoryContainer.appendChild(item);
        });
    }

    // --- 4. Suggestions Handler ---
    document.querySelectorAll(".suggestion").forEach(btn => {
        btn.addEventListener("click", () => {
            const q = btn.getAttribute("data-query");
            if (q) {
                userInput.value = q;
                handleSendMessage();
            }
        });
    });

    // --- 5. Message Submission & Streaming UI ---
    async function handleSendMessage() {
        const query = userInput.value.trim();
        if (!query) return;

        // Hide welcome message on first message
        welcomeMessage.style.display = "none";
        addChatToHistory(query);

        // Append User Message
        appendUserMessage(query);
        userInput.value = "";

        // Append Loading Indicator
        const loadingRow = appendLoadingIndicator();
        chatContainer.scrollTop = chatContainer.scrollHeight;

        try {
            const response = await fetch("/api/ask", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query: query, top_k: 5 })
            });

            const data = await response.json();
            loadingRow.remove();

            if (response.ok) {
                appendBotMessage(data.answer, data.evidence || []);
            } else {
                appendBotMessage(`Error: ${data.detail || "Failed to generate answer."}`, []);
            }
        } catch (err) {
            loadingRow.remove();
            appendBotMessage(`Connection Error: ${err.message}`, []);
        }

        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    sendBtn.addEventListener("click", handleSendMessage);
    userInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });

    // --- 6. Message Rendering Functions ---
    function appendUserMessage(text) {
        const row = document.createElement("div");
        row.className = "message-row user-row";
        row.innerHTML = `<div class="user-message">${escapeHtml(text)}</div>`;
        messagesList.appendChild(row);
    }

    function appendLoadingIndicator() {
        const row = document.createElement("div");
        row.className = "message-row bot-row";
        row.innerHTML = `
            <div class="loading-message">
                Auditing financial filings
                <span class="dots"><span></span><span></span><span></span></span>
            </div>
        `;
        messagesList.appendChild(row);
        return row;
    }

    function appendBotMessage(answerText, evidenceList) {
        const row = document.createElement("div");
        row.className = "message-row bot-row";

        // Store evidence globally for modal inspection
        evidenceList.forEach(ev => {
            currentEvidenceStore[ev.citation_id] = ev;
        });

        // Format Answer Markdown
        const renderedHtml = marked.parse(formatInlineCitations(answerText));

        let sourcesHtml = "";
        if (evidenceList.length > 0) {
            const cardsHtml = evidenceList.map(ev => `
                <div class="source-card" data-cid="${ev.citation_id}" title="Click to view verified chunk">
                    <span class="card-tag">${ev.citation_id}</span>
                    <span class="card-type">${ev.chunk_type}</span>
                    <span>${ev.document_name} · ${ev.page}</span>
                </div>
            `).join("");

            sourcesHtml = `
                <div class="sources">
                    <div class="sources-title">Verified Audit Sources (${evidenceList.length})</div>
                    <div class="source-cards-grid">${cardsHtml}</div>
                </div>
            `;
        }

        row.innerHTML = `
            <div class="bot-message">
                <div class="bot-header">
                    <span>🤖</span> Financial AI Auditor
                </div>
                <div class="bot-text">${renderedHtml}</div>
                ${sourcesHtml}
            </div>
        `;

        // Add Click Handlers for Sources and Inline Citation Links
        row.querySelectorAll(".source-card").forEach(card => {
            card.addEventListener("click", () => {
                const cid = card.getAttribute("data-cid");
                openEvidenceModal(cid);
            });
        });

        row.querySelectorAll(".citation-link").forEach(link => {
            link.addEventListener("click", (e) => {
                e.preventDefault();
                const cid = link.getAttribute("data-cid");
                openEvidenceModal(cid);
            });
        });

        messagesList.appendChild(row);
    }

    function formatInlineCitations(text) {
        // Replace [C1], [C2], [C1][C2] with interactive styled links
        return text.replace(/\[C(\d+)\]/g, (match, num) => {
            const cid = `[C${num}]`;
            return `<a href="#" class="citation-link" data-cid="${cid}" style="display:inline-block; font-weight:bold; color:#0066cc; text-decoration:none; background:#e6f0fa; padding:1px 6px; border-radius:4px; margin:0 2px; font-size:12px;">${match}</a>`;
        });
    }

    // --- 7. Evidence Inspection Modal ---
    function openEvidenceModal(citationId) {
        const ev = currentEvidenceStore[citationId];
        if (!ev) return;

        modalCitationTitle.textContent = `Evidence Source ${ev.citation_id} (${ev.chunk_type})`;
        modalCitationMeta.innerHTML = `
            <strong>Document:</strong> ${ev.document_name} &nbsp;|&nbsp;
            <strong>Location:</strong> ${ev.page} &nbsp;|&nbsp;
            <strong>Section:</strong> ${ev.section} &nbsp;|&nbsp;
            <strong>Relevance Score:</strong> ${ev.rerank_score.toFixed(4)}
        `;
        modalCitationBody.textContent = ev.content;
        evidenceModal.style.display = "flex";
    }

    closeModalBtn.addEventListener("click", () => {
        evidenceModal.style.display = "none";
    });

    evidenceModal.addEventListener("click", (e) => {
        if (e.target === evidenceModal) {
            evidenceModal.style.display = "none";
        }
    });

    // --- 8. File Upload Handler ---
    fileUpload.addEventListener("change", async (e) => {
        const files = Array.from(e.target.files);
        if (files.length === 0) return;

        uploadedFilesContainer.innerHTML = "";
        files.forEach(file => {
            const pill = document.createElement("div");
            pill.className = "uploaded-file";
            pill.innerHTML = `
                <span>📄 ${escapeHtml(file.name)}</span>
                <span style="color:#0066cc; font-size:11px;">Uploading...</span>
            `;
            uploadedFilesContainer.appendChild(pill);
        });

        const formData = new FormData();
        files.forEach(f => formData.append("files", f));

        try {
            const res = await fetch("/api/upload", {
                method: "POST",
                body: formData
            });
            const data = await res.json();
            uploadedFilesContainer.innerHTML = `
                <div class="uploaded-file" style="border-color:#22c55e; color:#15803d;">
                    <span>✓ Successfully indexed ${files.length} document(s)</span>
                </div>
            `;
            fetchDocuments();
            fetchSystemHealth();
            setTimeout(() => { uploadedFilesContainer.innerHTML = ""; }, 4000);
        } catch (err) {
            uploadedFilesContainer.innerHTML = `
                <div class="uploaded-file" style="border-color:#ef4444; color:#b91c1c;">
                    <span>✕ Upload failed: ${err.message}</span>
                </div>
            `;
        }
    });

    function escapeHtml(str) {
        return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    // Startup Initialization
    initNewChat();
    renderChatHistory();
    fetchSystemHealth();
    fetchDocuments();
});

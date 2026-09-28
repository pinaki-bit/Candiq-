/**
 * browser_extension/popup/popup.js
 * 
 * Logic script for Chrome extension popup UI.
 */

const API_BASE_URL = "http://localhost:8000/api/v1";

document.addEventListener("DOMContentLoaded", async () => {
    const authSection = document.getElementById("auth-section");
    const sourcerSection = document.getElementById("sourcer-section");
    const statusBox = document.getElementById("status-box");
    const btnLogin = document.getElementById("btn-login");
    const btnIngest = document.getElementById("btn-ingest");

    // Check stored JWT token
    const stored = await chrome.storage.local.get(["access_token"]);
    if (stored.access_token) {
        authSection.style.display = "none";
        sourcerSection.style.display = "block";
        triggerScrape();
    }

    btnLogin.addEventListener("click", async () => {
        const email = document.getElementById("login-email").value;
        const password = document.getElementById("login-pass").value;

        statusBox.className = "status-msg";
        statusBox.innerText = "Authenticating...";

        try {
            const resp = await fetch(`${API_BASE_URL}/auth/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password })
            });

            if (!resp.ok) {
                const err = await resp.json();
                throw new Error(err.detail || "Login failed");
            }

            const data = await resp.json();
            await chrome.storage.local.set({ access_token: data.access_token });
            
            statusBox.className = "status-msg success";
            statusBox.innerText = "✅ Connected!";
            authSection.style.display = "none";
            sourcerSection.style.display = "block";
            triggerScrape();
        } catch (err) {
            statusBox.className = "status-msg error";
            statusBox.innerText = `❌ ${err.message}`;
        }
    });

    btnIngest.addEventListener("click", async () => {
        const payload = {
            name: document.getElementById("cand-name").value,
            current_title: document.getElementById("cand-title").value,
            source_platform: "extension",
            skills: document.getElementById("cand-skills").value.split(",").map(s => s.trim()).filter(Boolean)
        };

        statusBox.className = "status-msg";
        statusBox.innerText = "Ingesting candidate into AI Pipeline...";

        chrome.runtime.sendMessage({ action: "INGEST_CANDIDATE", payload }, (response) => {
            if (response && response.success) {
                statusBox.className = "status-msg success";
                statusBox.innerText = `✅ Ingested! ID: ${response.data.candidate_id} | Domain: ${response.data.predicted_domain}`;
            } else {
                statusBox.className = "status-msg error";
                statusBox.innerText = `❌ ${response ? response.error : 'Failed to ingest'}`;
            }
        });
    });

    function triggerScrape() {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (tabs[0]) {
                chrome.tabs.sendMessage(tabs[0].id, { action: "SCRAPE_PROFILE" }, (response) => {
                    if (response && response.success && response.payload) {
                        const p = response.payload;
                        document.getElementById("cand-name").value = p.name || "";
                        document.getElementById("cand-title").value = p.current_title || "";
                    }
                });
            }
        });
    }
});

/**
 * browser_extension/background.js
 * 
 * Manifest v3 Service Worker for Resume Intelligence Extension.
 * Manages API token storage and dispatches ingestion requests.
 */

const API_BASE_URL = "http://localhost:8000/api/v1";

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "INGEST_CANDIDATE") {
        handleIngestCandidate(request.payload)
            .then(res => sendResponse({ success: true, data: res }))
            .catch(err => sendResponse({ success: false, error: err.message }));
        return true; // Keep sendResponse channel open for async response
    }
    
    if (request.action === "CHECK_API_STATUS") {
        fetch(`${API_BASE_URL}/extension/status`)
            .then(res => res.json())
            .then(data => sendResponse({ success: true, data }))
            .catch(err => sendResponse({ success: false, error: err.message }));
        return true;
    }
});

async function handleIngestCandidate(payload) {
    const tokenObj = await chrome.storage.local.get(["access_token"]);
    const token = tokenObj.access_token;
    
    if (!token) {
        throw new Error("Not authenticated with Resume Intelligence. Please log in via extension popup.");
    }
    
    const response = await fetch(`${API_BASE_URL}/extension/ingest`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify(payload)
    });
    
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Ingestion request failed");
    }
    
    return await response.json();
}

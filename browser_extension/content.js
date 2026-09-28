/**
 * browser_extension/content.js
 * 
 * Content script injected into LinkedIn, Indeed, and GitHub candidate pages.
 * Extracts profile metadata (Name, Headline/Title, Company, Skills, Summary, URL).
 */

function extractCandidateMetadata() {
    const url = window.location.href;
    let metadata = {
        name: "",
        current_title: "",
        company: "",
        profile_url: url,
        source_platform: "custom",
        summary: "",
        skills: []
    };

    if (url.includes("linkedin.com")) {
        metadata.source_platform = "linkedin";
        const nameEl = document.querySelector("h1.text-heading-xlarge, h1");
        if (nameEl) metadata.name = nameEl.innerText.trim();

        const titleEl = document.querySelector(".text-body-medium, div.text-body-medium");
        if (titleEl) metadata.current_title = titleEl.innerText.trim();

        const aboutEl = document.querySelector("#about ~ div .display-flex span");
        if (aboutEl) metadata.summary = aboutEl.innerText.trim();
    } else if (url.includes("github.com")) {
        metadata.source_platform = "github";
        const nameEl = document.querySelector(".p-name");
        const loginEl = document.querySelector(".p-nickname");
        metadata.name = nameEl ? nameEl.innerText.trim() : (loginEl ? loginEl.innerText.trim() : "");
        
        const bioEl = document.querySelector(".user-profile-bio");
        if (bioEl) metadata.summary = bioEl.innerText.trim();
        
        const companyEl = document.querySelector("li[itemprop='worksFor']");
        if (companyEl) metadata.company = companyEl.innerText.trim();
    } else if (url.includes("indeed.com")) {
        metadata.source_platform = "indeed";
        const nameEl = document.querySelector("h1, #resume-contact-name");
        if (nameEl) metadata.name = nameEl.innerText.trim();
    }

    if (!metadata.name) {
        metadata.name = document.title.split("-")[0].split("|")[0].trim() || "Candidate Profile";
    }

    return metadata;
}

// Listen for messages from extension popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "SCRAPE_PROFILE") {
        const data = extractCandidateMetadata();
        sendResponse({ success: true, payload: data });
    }
});

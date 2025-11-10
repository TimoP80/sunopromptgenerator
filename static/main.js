const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const fileInfo = document.getElementById('fileInfo');
const loading = document.getElementById('loading');
const error = document.getElementById('error');
const results = document.getElementById('results');
const analysisGrid = document.getElementById('analysisGrid');
const loadingStatus = document.getElementById('loadingStatus');
const progressBar = document.getElementById('progressBar');
const modelQualitySelect = document.getElementById('modelQualitySelect');
const addGenreBtn = document.getElementById('addGenreBtn');
const modal = document.getElementById('genreModal');
const closeBtn = document.querySelector('.close-btn');
const genreForm = document.getElementById('genreForm');
const clearBtn = document.getElementById('clearBtn');
const genreSelect = document.getElementById('genreSelect');
const metadataContainer = document.getElementById('metadataContainer');
const metadataGrid = document.getElementById('metadataGrid');
const proceedBtn = document.getElementById('proceedBtn');
const exportBtn = document.getElementById('exportBtn');
const themeToggle = document.getElementById('themeToggle');
const historyBtn = document.getElementById('historyBtn');
const historyPanel = document.getElementById('historyPanel');
const closeHistoryBtn = document.getElementById('closeHistoryBtn');
const historyContainer = document.getElementById('historyContainer');
const generationHistoryBtn = document.getElementById('generationHistoryBtn');
const generationHistoryPanel = document.getElementById('generationHistoryPanel');
const closeGenerationHistoryBtn = document.getElementById('closeGenerationHistoryBtn');
const generationHistoryContainer = document.getElementById('generationHistoryContainer');
const saveHistoryBtn = document.getElementById('saveHistoryBtn');
const settingsBtn = document.getElementById('settingsBtn');
const settingsModal = document.getElementById('settingsModal');
const settingsCloseBtn = document.getElementById('settingsCloseBtn');
const addAccountBtn = document.getElementById('addAccountBtn');
const accountsList = document.getElementById('accountsList');
const creditsDisplay = document.getElementById('credits-display');

let currentFile = null;
let currentFilepath = null;
let currentAnalysisResult = null;
let wavesurfer = null;

// --- Genre Population ---
async function populateGenres() {
    try {
        const response = await fetch('/api/genres');
        const genres = await response.json();
        genreSelect.innerHTML = genres.map(g => `<option value="${g.genre}">${g.genre}</option>`).join('');
    } catch (err) {
        console.error('Error fetching genres:', err);
    }
}

// --- Modal Logic ---
addGenreBtn.onclick = () => { modal.style.display = 'block'; }
closeBtn.onclick = () => { modal.style.display = 'none'; }
settingsCloseBtn.onclick = () => { settingsModal.style.display = 'none'; }

window.onclick = (event) => {
    if (event.target == modal) {
        modal.style.display = 'none';
    } else if (event.target == settingsModal) {
        settingsModal.style.display = 'none';
    }
}

settingsBtn.onclick = () => {
    settingsModal.style.display = 'block';
    loadAccounts();
}

genreForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const genreName = document.getElementById('genreName').value;
    const minBPM = document.getElementById('minBPM').value;
    const maxBPM = document.getElementById('maxBPM').value;

    try {
        const response = await fetch('/api/add_genre', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                genre_name: genreName,
                min_bpm: minBPM,
                max_bpm: maxBPM
            })
        });
        const result = await response.json();
        if (result.success) {
            alert(result.message);
            modal.style.display = 'none';
            genreForm.reset();
            populateGenres(); // Repopulate genres after adding a new one
        } else {
            throw new Error(result.error);
        }
    } catch (err) {
        alert(`Error adding genre: ${err.message}`);
    }
});

clearBtn.addEventListener('click', () => {
    fileInfo.classList.remove('active');
    results.classList.remove('active');
    error.classList.remove('active');
    fileInput.value = ''; // Reset file input
    clearBtn.style.display = 'none';
    uploadArea.style.display = 'block';
    fileInfo.textContent = '';
    exportBtn.style.display = 'none';
    if (wavesurfer) {
        wavesurfer.destroy();
    }
    document.getElementById('waveform').innerHTML = '';
});

exportBtn.addEventListener('click', () => {
    if (currentAnalysisResult) {
        exportResults(currentAnalysisResult);
    }
});

async function exportResults(data) {
    try {
        const response = await fetch('/api/export', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            throw new Error('Failed to export results.');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = 'analysis.json';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);

    } catch (err) {
        showError(err.message);
    }
}

// Click to upload
uploadArea.addEventListener('click', () => fileInput.click());

// Prevent default drag and drop behavior for the whole window
window.addEventListener('dragover', (e) => {
    e.preventDefault();
});

window.addEventListener('drop', (e) => {
    e.preventDefault();
});

// Drag and drop
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
});

// File input change
fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFile(e.target.files[0]);
    }
});

function handleFile(file) {
    currentFile = file;
    fileInfo.textContent = `Selected: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`;
    fileInfo.classList.add('active');
    
    results.classList.remove('active');
    error.classList.remove('active');
    metadataContainer.classList.remove('active');
    
    uploadArea.style.display = 'none';

    // Initialize WaveSurfer
    if (wavesurfer) {
        wavesurfer.destroy();
    }
    wavesurfer = WaveSurfer.create({
        container: '#waveform',
        waveColor: '#667eea',
        progressColor: '#764ba2',
        cursorWidth: 2,
        barWidth: 3,
        barRadius: 3,
        responsive: true,
        height: 100
    });
    wavesurfer.load(URL.createObjectURL(file));

    preprocessFile(file);
}

async function preprocessFile(file) {
    loading.classList.add('active');
    loadingStatus.textContent = 'Extracting metadata...';
    progressBar.style.width = '0%';

    const formData = new FormData();
    formData.append('audio', file);

    try {
        const response = await fetch('/api/preprocess', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        displayMetadata(data.metadata);
        currentFilepath = data.filepath;

    } catch (err) {
        showError(err.message);
    } finally {
        loading.classList.remove('active');
    }
}

function displayMetadata(metadata) {
    let metadataHTML = '';
    for (const [key, value] of Object.entries(metadata)) {
        metadataHTML += `
            <div class="analysis-item">
                <div class="analysis-label">${key}</div>
                <div class="analysis-value">${value}</div>
            </div>
        `;
    }

    metadataGrid.innerHTML = metadataHTML;
    metadataContainer.classList.add('active');
}

proceedBtn.addEventListener('click', () => {
    if (currentFile) {
        metadataContainer.classList.remove('active');
        uploadAndAnalyze(currentFile);
    }
});

async function uploadAndAnalyze(file) {
    loading.classList.add('active');
    loadingStatus.textContent = 'Starting analysis...';
    progressBar.style.width = '0%';
    
    const modelQuality = modelQualitySelect.value;
    const formData = new FormData();
    formData.append('audio', file);
    formData.append('model_quality', modelQuality);
    formData.append('selected_genre', genreSelect.value);
    formData.append('demucs_model', document.getElementById('separationQualitySelect').value);
    formData.append('save_vocals', document.getElementById('saveVocalsCheckbox').checked);

    try {
        const response = await fetch('/api/analyze', { // This is now a streaming endpoint
            method: 'POST',
            body: formData
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n\n');

            for (const line of lines) {
                if (line.startsWith('data:')) {
                    const dataStr = line.substring(5);
                    if (!dataStr) continue;
                    
                    const data = JSON.parse(dataStr);

                    if (data.error) {
                        throw new Error(data.error);
                    } else if (data.result) {
                        displayResults(data.result);
                    } else {
                        loadingStatus.textContent = data.status;
                        progressBar.style.width = `${data.progress}%`;
                    }
                }
            }
        }
    } catch (err) {
        showError(err.message);
    } finally {
        loading.classList.remove('active');
    }
}

function escapeTemplateLiteral(str) {
    if (str === null || str === undefined) {
        return '';
    }
    // Escape backticks and template literal placeholders
    return String(str).replace(/`/g, '\\`').replace(/\${/g, '\\${');
}

function openTab(evt, tabName) {
    const tabContents = document.getElementsByClassName("tab-content");
    for (let i = 0; i < tabContents.length; i++) {
        tabContents[i].classList.remove("active");
    }
    const tabLinks = document.getElementsByClassName("tab-link");
    for (let i = 0; i < tabLinks.length; i++) {
        tabLinks[i].classList.remove("active");
    }
    document.getElementById(tabName).classList.add("active");
    evt.currentTarget.classList.add("active");
}

function displayResults(data) {
    currentAnalysisResult = data;
    const { analysis, prompts } = data;

    // Display analysis
    analysisGrid.innerHTML = `
        <div class="analysis-item">
            <div class="analysis-label">Tempo</div>
            <div class="analysis-value">${analysis.tempo} BPM</div>
        </div>
        <div class="analysis-item">
            <div class="analysis-label">Key</div>
            <div class="analysis-value">${analysis.key}</div>
        </div>
        <div class="analysis-item">
            <div class="analysis-label">Energy</div>
            <div class="analysis-value">${analysis.energy}</div>
        </div>
        <div class="analysis-item">
            <div class="analysis-label">Genre</div>
            <div class="analysis-value">${analysis.genre}</div>
        </div>
        <div class="analysis-item">
            <div class="analysis-label">Mood</div>
            <div class="analysis-value">${analysis.mood}</div>
        </div>
        <div class="analysis-item">
            <div class="analysis-label">Vocals</div>
            <div class="analysis-value">${analysis.has_vocals ? 'Yes' : 'No'}</div>
        </div>
    `;

    // Categorize prompts
    const standardPrompts = prompts.filter(p => ["Basic", "Detailed", "Style-Focused", "Tempo-Focused"].includes(p.name));
    const creativePrompts = prompts.filter(p => ["Thematic", "Artist Style", "Refinement Prompt"].includes(p.name));
    const advancedPrompts = prompts.filter(p => p.name === "Advanced Mode");

    // Display prompts in their respective tabs
    document.getElementById('standardPrompts').innerHTML = standardPrompts.map((p, index) => createPromptCard(p, `std-${index}`)).join('');
    document.getElementById('creativePrompts').innerHTML = creativePrompts.map((p, index) => createPromptCard(p, `creative-${index}`)).join('');
    document.getElementById('advancedPrompts').innerHTML = advancedPrompts.map((p, index) => createPromptCard(p, `adv-${index}`)).join('');

    results.classList.add('active');
    clearBtn.style.display = 'inline-block'; // Show clear button
    exportBtn.style.display = 'inline-block';
    saveHistoryBtn.style.display = 'inline-block';
}

function createPromptCard(p, index) {
    const isAdvanced = p.name === 'Advanced Mode';
    const promptId = `prompt-text-${index}`;
    const stylePromptId = `style-prompt-${index}`;
    const lyricsPromptId = `lyrics-prompt-${index}`;

    if (isAdvanced) {
        return `
            <div class="prompt-card">
                <div class="prompt-header">
                    <span class="prompt-name">Advanced Prompt</span>
                    <button class="generate-btn" onclick="generateMusic('${p.name}', {style: '${stylePromptId}', lyrics: '${lyricsPromptId}', title: 'title-${index}', tags: 'tags-${index}'})">Generate Music</button>
                </div>
                <div class="generation-inputs">
                    <input type="text" id="title-${index}" placeholder="Title (optional)">
                    <input type="text" id="tags-${index}" placeholder="Tags (optional)">
                </div>
                <div class="prompt-subsection">
                    <div class="prompt-header">
                        <span class="prompt-name-sub">Style of Music</span>
                        <button class="copy-btn" onclick="copyPrompt('${stylePromptId}', this)">Copy Style</button>
                    </div>
                    <div class="prompt-text">
                        <textarea id="${stylePromptId}">${escapeTemplateLiteral(p.prompt.style_prompt || '')}</textarea>
                    </div>
                </div>
                <div class="prompt-subsection">
                    <div class="prompt-header">
                        <span class="prompt-name-sub">Lyrics Template</span>
                        <button class="copy-btn" onclick="copyPrompt('${lyricsPromptId}', this)">Copy Lyrics</button>
                    </div>
                    <div class="prompt-text">
                        <textarea id="${lyricsPromptId}">${escapeTemplateLiteral(p.prompt.lyrics_prompt)}</textarea>
                    </div>
                </div>
            </div>`;
    } else {
        return `
            <div class="prompt-card">
                <div class="prompt-header">
                    <span class="prompt-name">${p.name}</span>
                    <div>
                        <button class="copy-btn" onclick="copyPrompt('${promptId}', this)">Copy</button>
                        <button class="generate-btn" onclick="generateMusic('${p.name}', '${promptId}', 'title-${index}', 'tags-${index}')">Generate Music</button>
                    </div>
                </div>
                <div class="generation-inputs">
                    <input type="text" id="title-${index}" placeholder="Title (optional)">
                    <input type="text" id="tags-${index}" placeholder="Tags (optional)">
                </div>
                <div class="prompt-text">
                    <textarea id="${promptId}">${escapeTemplateLiteral(p.prompt || '')}</textarea>
                </div>
            </div>`;
    }
}

function copyPrompt(elementId, button) {
    const promptElement = document.getElementById(elementId);
    const promptText = promptElement.tagName === 'TEXTAREA' ? promptElement.value : promptElement.textContent;
    navigator.clipboard.writeText(promptText).then(() => {
        button.textContent = 'Copied!';
        button.classList.add('copied');
        setTimeout(() => {
            button.textContent = 'Copy';
            button.classList.remove('copied');
        }, 2000);
    });
}

function showError(message) {
    error.textContent = 'Error: ' + message;
    error.classList.add('active');
}

async function generateMusic(promptName, ids, titleId, tagsId) {
    const isCustom = promptName === 'Advanced Mode';
    const title = titleId ? document.getElementById(titleId).value : '';
    const tags = tagsId ? document.getElementById(tagsId).value : '';
    
    let payload = {
        is_custom: isCustom,
        title: title,
        tags: tags,
        prompt_name: promptName
    };

    if (isCustom) {
        payload.prompt = {
            style_prompt: document.getElementById(ids.style).value,
            lyrics_prompt: document.getElementById(ids.lyrics).value
        };
        // If tags are not provided in their own field, use the style prompt
        if (!payload.tags) {
            payload.tags = payload.prompt.style_prompt;
        }
    } else {
        payload.prompt = document.getElementById(ids).value;
    }

    await _executeGeneration(promptName, payload);
}

async function pollGenerationStatus(requestId, cardElement) {
    const statusElement = cardElement.querySelector('.generation-status');
    const spinnerElement = cardElement.querySelector('.spinner');
    const progressBar = cardElement.querySelector('.generation-progress-bar');
    const totalTracks = requestId.split(',').length;

    try {
        const apiKey = document.getElementById('apiKey').value;
        const response = await fetch(`/api/generation-status/${requestId}`, {
            headers: {
                'Authorization': `Bearer ${apiKey}`
            }
        });
        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        const completedTracks = data.results ? data.results.length : 0;
        const progress = totalTracks > 0 ? (completedTracks / totalTracks) * 100 : 0;
        
        statusElement.textContent = `Status: ${data.status.title()} (${completedTracks}/${totalTracks} complete)`;
        progressBar.style.width = `${progress}%`;

        if (data.status === 'completed' && data.results) {
            spinnerElement.style.display = 'none';
            displayGeneratedAudio(data.results, cardElement);
        } else if (data.status === 'failed') {
            spinnerElement.style.display = 'none';
            throw new Error(data.message || 'Generation failed.');
        } else {
            setTimeout(() => pollGenerationStatus(requestId, cardElement), 5000); // Poll every 5 seconds
        }

    } catch (err) {
        let errorMessage = err.message;
        // Try to parse a more specific error from the response
        try {
            const errorJson = JSON.parse(err.message);
            if (errorJson.detail) {
                errorMessage = errorJson.detail;
            }
        } catch (e) {
            // Not a JSON error, use the original message
        }
        statusElement.textContent = `Error: ${errorMessage}`;
        statusElement.classList.add('generation-error');
        spinnerElement.style.display = 'none';
    }
}

function displayGeneratedAudio(results, cardElement) {
    const audioContainer = document.createElement('div');
    audioContainer.className = 'audio-container';
    results.forEach(result => {
        const trackElement = document.createElement('div');
        trackElement.className = 'audio-track';

        const audio = new Audio(result.audio_url);
        audio.controls = true;
        
        const downloadBtn = document.createElement('button');
        downloadBtn.className = 'btn btn-secondary';
        downloadBtn.textContent = 'Download';
        downloadBtn.onclick = () => downloadAudio(result.audio_url, result.title);

        trackElement.appendChild(audio);
        trackElement.appendChild(downloadBtn);
        audioContainer.appendChild(trackElement);
    });
    cardElement.appendChild(audioContainer);
}

async function downloadAudio(audioUrl, title) {
    try {
        const apiKey = document.getElementById('apiKey').value;
        const response = await fetch(`/api/download-audio?url=${encodeURIComponent(audioUrl)}&title=${encodeURIComponent(title)}`, {
            headers: {
                'Authorization': `Bearer ${apiKey}`
            }
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to download audio.');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `${title}.mp3`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();

    } catch (err) {
        alert(`Error downloading audio: ${err.message}`);
    }
}

function openQuickGenTab(evt, tabName) {
    const tabContents = document.getElementsByClassName("quick-generation-tab-content");
    for (let i = 0; i < tabContents.length; i++) {
        tabContents[i].classList.remove("active");
    }
    const tabLinks = document.querySelectorAll(".quick-generation-tabs .tab-link");
    for (let i = 0; i < tabLinks.length; i++) {
        tabLinks[i].classList.remove("active");
    }
    document.getElementById(tabName).classList.add("active");
    evt.currentTarget.classList.add("active");
}

async function handleQuickGenerate() {
    const activeTab = document.querySelector('.quick-generation-tab-content.active').id;
    const title = document.getElementById('quickGenTitle').value;
    const instrumental = document.getElementById('quickGenInstrumental').checked;
    
    let payload;
    let promptName;

    if (activeTab === 'quickGenSimple') {
        const simplePrompt = document.getElementById('quickGenSimplePrompt').value;
        if (!simplePrompt.trim()) {
            alert('Please enter a prompt.');
            return;
        }
        payload = {
            prompt: simplePrompt,
            is_custom: false,
            title: title || 'AI Music (Simple)',
            instrumental: instrumental,
            tags: simplePrompt.split(',').slice(0, 3).join(', ') // Basic tags from prompt
        };
        promptName = "Quick Gen (Simple)";
    } else {
        const advancedStyle = document.getElementById('quickGenAdvancedStyle').value;
        const advancedLyrics = document.getElementById('quickGenAdvancedLyrics').value;
        if (!advancedStyle.trim() && !advancedLyrics.trim()) {
            alert('Please enter a style or lyrics for advanced generation.');
            return;
        }
        payload = {
            prompt: {
                style_prompt: advancedStyle,
                lyrics_prompt: advancedLyrics
            },
            is_custom: true,
            title: title || 'AI Music (Advanced)',
            tags: advancedStyle,
            instrumental: instrumental
        };
        promptName = "Quick Gen (Advanced)";
    }

    await _executeGeneration(promptName, payload);
}

async function _executeGeneration(promptName, payload) {
    openTab({ currentTarget: document.querySelector('.tab-link[onclick*="sunoGenerations"]') }, 'sunoGenerations');
    
    const generationsContainer = document.getElementById('generationsContainer');
    const generationCard = document.createElement('div');
    generationCard.className = 'generation-card';
    generationCard.innerHTML = `
        <div class="generation-header">
            <span class="generation-name">Generating: ${promptName}</span>
            <div class="spinner"></div>
        </div>
        <div class="generation-status">Status: Queued</div>
        <div class="generation-progress-container">
            <div class="generation-progress-bar"></div>
        </div>
    `;
    generationsContainer.appendChild(generationCard);

    try {
        const apiKey = document.getElementById('apiKey').value;
        if (!apiKey) {
            alert('Please enter your Suno API key.');
            generationCard.querySelector('.generation-status').textContent = 'Error: API Key is missing.';
            generationCard.querySelector('.spinner').style.display = 'none';
            return;
        }

        const response = await fetch('/api/generate-music', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${apiKey}`
            },
            body: JSON.stringify(payload)
        });
        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        const generationIds = data.map(clip => clip.id).join(',');
        pollGenerationStatus(generationIds, generationCard);

       fetchCredits(); // Refresh credits after generation

    } catch (err) {
        const statusElement = generationCard.querySelector('.generation-status');
        let errorMessage = err.message;
        try {
            const errorJson = JSON.parse(err.message);
            if (errorJson.detail) {
                errorMessage = errorJson.detail;
            }
        } catch (e) {
            // Not a JSON error, use the original message
        }
        statusElement.textContent = `Error: ${errorMessage}`;
        statusElement.classList.add('generation-error');
        generationCard.querySelector('.spinner').style.display = 'none';
    }
}


// --- Account Management ---
async function loadAccounts() {
    try {
        const response = await fetch('/api/accounts');
        const accounts = await response.json();
        renderAccounts(accounts);
    } catch (err) {
        console.error('Error loading accounts:', err);
        accountsList.innerHTML = '<p>Could not load accounts.</p>';
    }
}

function renderAccounts(accounts) {
    if (Object.keys(accounts).length === 0) {
        accountsList.innerHTML = '<p>No accounts configured.</p>';
        return;
    }
    accountsList.innerHTML = Object.entries(accounts).map(([name, data]) => `
        <div class="account-item ${data.default ? 'default' : ''}">
            <span>${name} ${data.default ? '(Default)' : ''}</span>
            <div>
                <button class="btn btn-secondary" onclick="setDefaultAccount('${name}')">Set Default</button>
                <button class="btn btn-danger" onclick="removeAccount('${name}')">Remove</button>
            </div>
        </div>
    `).join('');
}

async function addAccount() {
    const name = document.getElementById('accountName').value;
    const apiKey = document.getElementById('accountApiKey').value;

    if (!name.trim() || !apiKey.trim()) {
        alert('Please provide both an account name and an API key.');
        return;
    }

    try {
        const response = await fetch('/api/accounts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, api_key: apiKey })
        });
        const result = await response.json();
        if (result.success) {
            document.getElementById('accountName').value = '';
            document.getElementById('accountApiKey').value = '';
            loadAccounts();
            fetchCredits(); // Refresh credits after adding a new default
        } else {
            throw new Error(result.error);
        }
    } catch (err) {
        alert(`Error adding account: ${err.message}`);
    }
}

async function removeAccount(name) {
    if (!confirm(`Are you sure you want to remove the account "${name}"?`)) {
        return;
    }
    try {
        const response = await fetch('/api/accounts', {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        });
        const result = await response.json();
        if (result.success) {
            loadAccounts();
            fetchCredits(); // Refresh credits if the default was removed
        } else {
            throw new Error(result.error);
        }
    } catch (err) {
        alert(`Error removing account: ${err.message}`);
    }
}

async function setDefaultAccount(name) {
    try {
        const response = await fetch('/api/accounts/default', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        });
        const result = await response.json();
        if (result.success) {
            loadAccounts();
            fetchCredits(); // Refresh credits with the new default account
        } else {
            throw new Error(result.error);
        }
    } catch (err) {
        alert(`Error setting default account: ${err.message}`);
    }
}

async function fetchCredits() {
    const apiKey = document.getElementById('apiKey').value;
    if (!apiKey) {
        creditsDisplay.textContent = 'N/A';
        return;
    }
    try {
        const response = await fetch('/api/credits', {
            headers: { 'Authorization': `Bearer ${apiKey}` }
        });
        const data = await response.json();
        if (data.error) {
            creditsDisplay.textContent = 'Error';
            console.error('Error fetching credits:', data.error);
        } else {
            creditsDisplay.textContent = data.credits;
        }
    } catch (err) {
        creditsDisplay.textContent = 'Error';
        console.error('Error fetching credits:', err);
    }
}


// Initial population of genres
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('quickGenerateBtn').addEventListener('click', handleQuickGenerate);
    addAccountBtn.addEventListener('click', addAccount);
    populateGenres();
    fetchCredits(); // Initial fetch
    setInterval(fetchCredits, 60000); // Refresh credits every 60 seconds

    // --- API Key Persistence ---
    const apiKeyInput = document.getElementById('apiKey');
    const savedApiKey = localStorage.getItem('sunoApiKey');
    if (savedApiKey) {
        apiKeyInput.value = savedApiKey;
    }

    apiKeyInput.addEventListener('input', () => {
        localStorage.setItem('sunoApiKey', apiKeyInput.value);
    });

    // --- Theme Switcher Logic ---
    const currentTheme = localStorage.getItem('theme');
    if (currentTheme === 'dark') {
        document.body.classList.add('dark-mode');
        themeToggle.checked = true;
    }

    themeToggle.addEventListener('change', () => {
        if (themeToggle.checked) {
            document.body.classList.add('dark-mode');
            localStorage.setItem('theme', 'dark');
        } else {
            document.body.classList.remove('dark-mode');
            localStorage.setItem('theme', 'light');
        }
    });

    // --- History Panel Logic ---
    historyBtn.addEventListener('click', () => {
        historyPanel.classList.add('open');
        loadHistory();
    });

    closeHistoryBtn.addEventListener('click', () => {
        historyPanel.classList.remove('open');
    });

    generationHistoryBtn.addEventListener('click', () => {
        generationHistoryPanel.classList.add('open');
        loadGenerationHistory();
    });

    closeGenerationHistoryBtn.addEventListener('click', () => {
        generationHistoryPanel.classList.remove('open');
    });

    saveHistoryBtn.addEventListener('click', async () => {
        if (currentAnalysisResult) {
            try {
                const response = await fetch('/api/history', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(currentAnalysisResult)
                });
                const result = await response.json();
                if (result.success) {
                    alert('Analysis saved to history!');
                } else {
                    throw new Error(result.error);
                }
            } catch (err) {
                alert(`Error saving to history: ${err.message}`);
            }
        }
    });

    async function loadHistory() {
        try {
            const response = await fetch('/api/history');
            const history = await response.json();
            historyContainer.innerHTML = history.map(item => `
                <div class="history-item" data-id="${item.id}">
                    <div class="history-item-date">${new Date(item.timestamp).toLocaleString()}</div>
                    <div class="history-item-genre">${item.analysis.genre}</div>
                </div>
            `).join('');

            // Add event listeners to history items
            document.querySelectorAll('.history-item').forEach(item => {
                item.addEventListener('click', () => {
                    const selected = history.find(h => h.id === item.dataset.id);
                    if (selected) {
                        displayResults(selected);
                        historyPanel.classList.remove('open');
                    }
                });
            });

        } catch (err) {
            historyContainer.innerHTML = '<p>Could not load history.</p>';
        }
    }

    async function loadGenerationHistory() {
        try {
            const response = await fetch('/api/generation-history');
            const history = await response.json();
            generationHistoryContainer.innerHTML = history.map(item => `
                <div class="history-item" data-id="${item.id}">
                    <div class="history-item-date">${new Date(item.timestamp).toLocaleString()}</div>
                    <div class="history-item-title">${item.title || 'Untitled'}</div>
                </div>
            `).join('');

            // Add event listeners to history items
            document.querySelectorAll('#generationHistoryContainer .history-item').forEach(item => {
                item.addEventListener('click', () => {
                    const selected = history.find(h => h.id === item.dataset.id);
                    if (selected) {
                        // We can't fully "load" a generation, but we can show it in the UI
                        openTab({ currentTarget: document.querySelector('.tab-link[onclick*="sunoGenerations"]') }, 'sunoGenerations');
                        const generationsContainer = document.getElementById('generationsContainer');
                        const generationCard = document.createElement('div');
                        generationCard.className = 'generation-card';
                        displayGeneratedAudio([selected], generationCard);
                        generationsContainer.prepend(generationCard);
                        generationHistoryPanel.classList.remove('open');
                    }
                });
            });

        } catch (err) {
            generationHistoryContainer.innerHTML = '<p>Could not load generation history.</p>';
        }
    }
});
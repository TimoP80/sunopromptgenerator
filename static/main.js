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
const saveHistoryBtn = document.getElementById('saveHistoryBtn');

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
window.onclick = (event) => {
    if (event.target == modal) {
        modal.style.display = 'none';
    }
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
                    <button class="generate-btn" onclick="generateMusic('${p.name}', {style: '${stylePromptId}', lyrics: '${lyricsPromptId}'})">Generate Music</button>
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
                        <button class="generate-btn" onclick="generateMusic('${p.name}', '${promptId}')">Generate Music</button>
                    </div>
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

async function generateMusic(promptName, ids) {
    let promptPayload;
    const isCustom = promptName === 'Advanced Mode';

    if (isCustom) {
        const stylePrompt = document.getElementById(ids.style).value;
        const lyricsPrompt = document.getElementById(ids.lyrics).value;
        promptPayload = {
            style_prompt: stylePrompt,
            lyrics_prompt: lyricsPrompt
        };
    } else {
        promptPayload = document.getElementById(ids).value;
    }

    // Switch to the generations tab
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
    `;
    generationsContainer.appendChild(generationCard);

    try {
        const response = await fetch('/api/generate-music', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prompt: promptPayload,
                is_custom: isCustom,
                prompt_name: promptName
            })
        });
        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        pollGenerationStatus(data.request_id, generationCard);

    } catch (err) {
        const statusElement = generationCard.querySelector('.generation-status');
        statusElement.textContent = `Error: ${err.message}`;
        statusElement.classList.add('generation-error');
        generationCard.querySelector('.spinner').style.display = 'none';
    }
}

async function pollGenerationStatus(requestId, cardElement) {
    const statusElement = cardElement.querySelector('.generation-status');
    const spinnerElement = cardElement.querySelector('.spinner');

    try {
        const response = await fetch(`/api/generation-status/${requestId}`);
        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        statusElement.textContent = `Status: ${data.status}`;

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
        statusElement.textContent = `Error: ${err.message}`;
        statusElement.classList.add('generation-error');
        spinnerElement.style.display = 'none';
    }
}

function displayGeneratedAudio(results, cardElement) {
    const audioContainer = document.createElement('div');
    audioContainer.className = 'audio-container';
    results.forEach(result => {
        const audio = new Audio(result.audio_url);
        audio.controls = true;
        audioContainer.appendChild(audio);
    });
    cardElement.appendChild(audioContainer);
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
    const simplePrompt = document.getElementById('quickGenSimplePrompt').value;
    const advancedStyle = document.getElementById('quickGenAdvancedStyle').value;
    const advancedLyrics = document.getElementById('quickGenAdvancedLyrics').value;
    const title = document.getElementById('quickGenTitle').value;
    const instrumental = document.getElementById('quickGenInstrumental').checked;

    const activeTab = document.querySelector('.quick-generation-tab-content.active').id;
    
    let requestBody;
    let promptName;

    if (activeTab === 'quickGenSimple') {
        if (!simplePrompt.trim()) {
            alert('Please enter a prompt.');
            return;
        }
        requestBody = {
            prompt: simplePrompt,
            is_custom: false,
            title: title || 'AI Music (Simple)',
            instrumental: instrumental
        };
        promptName = "Quick Gen (Simple)";
    } else {
        if (!advancedStyle.trim() && !advancedLyrics.trim()) {
            alert('Please enter a style or lyrics for advanced generation.');
            return;
        }
        requestBody = {
            prompt: {
                style_prompt: advancedStyle,
                lyrics_prompt: advancedLyrics
            },
            is_custom: true,
            title: title || 'AI Music (Advanced)',
            instrumental: instrumental
        };
        promptName = "Quick Gen (Advanced)";
    }

    // Reuse the existing generateMusic function's logic but adapted for this new flow
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
    `;
    generationsContainer.appendChild(generationCard);

    try {
        const response = await fetch('/api/generate-music', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });
        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        pollGenerationStatus(data.request_id, generationCard);

    } catch (err) {
        const statusElement = generationCard.querySelector('.generation-status');
        statusElement.textContent = `Error: ${err.message}`;
        statusElement.classList.add('generation-error');
        generationCard.querySelector('.spinner').style.display = 'none';
    }
}


// Initial population of genres
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('quickGenerateBtn').addEventListener('click', handleQuickGenerate);
    populateGenres();

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
});
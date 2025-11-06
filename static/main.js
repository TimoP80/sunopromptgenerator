const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const fileInfo = document.getElementById('fileInfo');
const loading = document.getElementById('loading');
const error = document.getElementById('error');
const results = document.getElementById('results');
const analysisGrid = document.getElementById('analysisGrid');
const promptsContainer = document.getElementById('promptsContainer');
const loadingStatus = document.getElementById('loadingStatus');
const progressBar = document.getElementById('progressBar');
const modelQualitySelect = document.getElementById('modelQualitySelect');
const addGenreBtn = document.getElementById('addGenreBtn');
const modal = document.getElementById('genreModal');
const closeBtn = document.querySelector('.close-btn');
const genreForm = document.getElementById('genreForm');
const clearBtn = document.getElementById('clearBtn');
const genreSelect = document.getElementById('genreSelect');

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
});

// Click to upload
uploadArea.addEventListener('click', () => fileInput.click());

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
    // Show file info
    fileInfo.textContent = `Selected: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`;
    fileInfo.classList.add('active');
    
    // Hide previous results and errors
    results.classList.remove('active');
    error.classList.remove('active');
    
    // Hide upload area to prevent another upload while one is in progress
    uploadArea.style.display = 'none';

    // Upload and analyze
    uploadAndAnalyze(file);
}

async function uploadAndAnalyze(file) {
    loading.classList.add('active');
    loadingStatus.textContent = 'Uploading file...';
    progressBar.style.width = '0%';
    
    const modelQuality = modelQualitySelect.value;
    const formData = new FormData();
    formData.append('audio', file);
    formData.append('model_quality', modelQuality);
    formData.append('selected_genre', genreSelect.value);

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

function displayResults(data) {
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

    // Display prompts
    promptsContainer.innerHTML = prompts.map((p, index) => `
        ${p.name === 'Advanced Mode' ? `
            <div class="prompt-card">
                <div class="prompt-header">
                    <span class="prompt-name">Advanced Prompt</span>
                </div>
                <div class="prompt-subsection">
                    <div class="prompt-header">
                        <span class="prompt-name-sub">Style of Music</span>
                        <button class="copy-btn" onclick="copyPrompt('style-prompt-${index}', this)">Copy Style</button>
                    </div>
                    <div class="prompt-text" id="style-prompt-${index}">${escapeTemplateLiteral(p.prompt.style_prompt || '')}</div>
                </div>
                <div class="prompt-subsection">
                    <div class="prompt-header">
                        <span class="prompt-name-sub">Lyrics Template</span>
                        <button class="copy-btn" onclick="copyPrompt('lyrics-prompt-${index}', this)">Copy Lyrics</button>
                    </div>
                    <div class="prompt-text">
                        <textarea id="lyrics-prompt-${index}" readonly>${escapeTemplateLiteral(p.prompt.lyrics_prompt)}</textarea>
                    </div>
                </div>
            </div>
        ` : `
            <div class="prompt-card">
                <div class="prompt-header">
                    <span class="prompt-name">${p.name}</span>
                    <button class="copy-btn" onclick="copyPrompt('prompt-text-${index}', this)">Copy</button>
                </div>
                <div class="prompt-text" id="prompt-text-${index}">${escapeTemplateLiteral(p.prompt || '')}</div>
            </div>
        `}
    `).join('');

    results.classList.add('active');
    clearBtn.style.display = 'inline-block'; // Show clear button
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

// Initial population of genres
document.addEventListener('DOMContentLoaded', populateGenres);
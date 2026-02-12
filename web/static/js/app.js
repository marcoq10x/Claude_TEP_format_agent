/**
 * AI FORMAT - LLM Output Formatter
 * Main Application JavaScript
 */

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const inputText = document.getElementById('input-text');
    const outputContent = document.getElementById('output-content');
    const practiceBtn = document.getElementById('practice-btn');
    const finalBtn = document.getElementById('final-btn');
    const downloadButtons = document.getElementById('download-buttons');
    const charCount = document.getElementById('char-count');
    const qCount = document.getElementById('q-count');
    const aCount = document.getElementById('a-count');
    const loadingOverlay = document.getElementById('loading-overlay');
    const toast = document.getElementById('toast');

    // Tab elements
    const inputTabs = document.querySelectorAll('.input-tab');
    const pasteTab = document.getElementById('paste-tab');
    const uploadTab = document.getElementById('upload-tab');
    const pasteInfo = document.getElementById('paste-info');
    const fileInfo = document.getElementById('file-info');
    const fileCountSpan = document.getElementById('file-count');

    // File upload elements
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const fileList = document.getElementById('file-list');

    // State
    let currentText = '';
    let currentExamType = null;
    let formattedData = null;
    let currentMode = 'paste'; // 'paste' or 'upload'
    let uploadedFiles = []; // Array of {name, content} objects

    // Tab switching
    inputTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.dataset.tab;
            switchTab(tabName);
        });
    });

    function switchTab(tabName) {
        currentMode = tabName;

        // Update tab buttons
        inputTabs.forEach(t => {
            t.classList.toggle('active', t.dataset.tab === tabName);
        });

        // Update tab content
        if (tabName === 'paste') {
            pasteTab.classList.add('active');
            uploadTab.classList.remove('active');
            pasteInfo.style.display = '';
            fileInfo.style.display = 'none';
        } else {
            pasteTab.classList.remove('active');
            uploadTab.classList.add('active');
            pasteInfo.style.display = 'none';
            fileInfo.style.display = '';
        }
    }

    // Character count update
    inputText.addEventListener('input', () => {
        charCount.textContent = inputText.value.length.toLocaleString();
        currentText = inputText.value;
    });

    // Drag and drop handling
    dropZone.addEventListener('click', () => {
        fileInput.click();
    });

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });

    dropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        handleFiles(e.dataTransfer.files);
    });

    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });

    async function handleFiles(files) {
        const maxFiles = 20;
        const validFiles = Array.from(files).filter(f => f.name.endsWith('.txt'));

        if (validFiles.length === 0) {
            showToast('Please upload .txt files only', 'error');
            return;
        }

        if (uploadedFiles.length + validFiles.length > maxFiles) {
            showToast(`Maximum ${maxFiles} files allowed`, 'error');
            return;
        }

        for (const file of validFiles) {
            try {
                const content = await readFileContent(file);
                uploadedFiles.push({
                    name: file.name,
                    content: content,
                    size: file.size
                });
            } catch (err) {
                console.error(`Error reading ${file.name}:`, err);
                showToast(`Failed to read ${file.name}`, 'error');
            }
        }

        updateFileList();
        fileInput.value = ''; // Reset input
    }

    function readFileContent(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = (e) => reject(e);
            reader.readAsText(file);
        });
    }

    function updateFileList() {
        fileCountSpan.textContent = uploadedFiles.length;

        if (uploadedFiles.length === 0) {
            fileList.innerHTML = '';
            return;
        }

        let html = '';
        uploadedFiles.forEach((file, index) => {
            const sizeKB = (file.size / 1024).toFixed(1);
            html += `
                <div class="file-item" data-index="${index}">
                    <div class="file-info">
                        <svg class="file-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M14 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V8L14 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            <path d="M14 2V8H20" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                        <span class="file-name">${escapeHtml(file.name)}</span>
                        <span class="file-size">${sizeKB} KB</span>
                    </div>
                    <button class="file-remove" data-index="${index}" title="Remove file">
                        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M18 6L6 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            <path d="M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </button>
                </div>
            `;
        });

        fileList.innerHTML = html;

        // Add remove button listeners
        fileList.querySelectorAll('.file-remove').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const index = parseInt(btn.dataset.index);
                uploadedFiles.splice(index, 1);
                updateFileList();
            });
        });
    }

    // Practice Exam button click
    practiceBtn.addEventListener('click', async () => {
        if (currentMode === 'paste') {
            const text = inputText.value.trim();
            if (!text) {
                showToast('Please enter some text to format', 'error');
                return;
            }
            currentExamType = 'practice';
            await formatText(text, 'practice');
        } else {
            if (uploadedFiles.length === 0) {
                showToast('Please upload at least one file', 'error');
                return;
            }
            currentExamType = 'practice';
            await formatMultipleFiles('practice');
        }
    });

    // Final Exam button click
    finalBtn.addEventListener('click', async () => {
        if (currentMode === 'paste') {
            const text = inputText.value.trim();
            if (!text) {
                showToast('Please enter some text to format', 'error');
                return;
            }
            currentExamType = 'final';
            await formatText(text, 'final');
        } else {
            if (uploadedFiles.length === 0) {
                showToast('Please upload at least one file', 'error');
                return;
            }
            currentExamType = 'final';
            await formatMultipleFiles('final');
        }
    });

    // Download button clicks
    downloadButtons.querySelectorAll('.download-button').forEach(btn => {
        btn.addEventListener('click', async () => {
            const format = btn.dataset.format;

            if (!currentExamType) {
                showToast('Please format the text first using Practice or Final Exam', 'error');
                return;
            }

            if (currentMode === 'paste') {
                const text = inputText.value.trim();
                if (!text) {
                    showToast('Please enter some text first', 'error');
                    return;
                }
                await downloadFile(text, format, currentExamType);
            } else {
                if (uploadedFiles.length === 0) {
                    showToast('Please upload at least one file', 'error');
                    return;
                }
                await downloadBatch(format, currentExamType);
            }
        });
    });

    // Keyboard shortcuts (Ctrl/Cmd + Enter for practice, Ctrl/Cmd + Shift + Enter for final)
    inputText.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            if (e.shiftKey) {
                finalBtn.click();
            } else {
                practiceBtn.click();
            }
        }
    });

    /**
     * Format the input text with the specified exam type
     */
    async function formatText(text, examType) {
        showLoading(true);

        try {
            const response = await fetch('/api/format', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text, exam_type: examType }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Formatting failed');
            }

            formattedData = data;
            displayFormattedOutput(data, examType);
            updateStats(data.stats);

            // Show warning if question/answer counts don't match
            if (data.warning) {
                showToast(data.warning, 'error');
            } else {
                const label = examType === 'practice' ? 'Practice Exam' : 'Final Exam';
                showToast(`Formatted as ${label} successfully!`, 'success');
            }

        } catch (error) {
            console.error('Format error:', error);
            showToast(error.message || 'An error occurred', 'error');
        } finally {
            showLoading(false);
        }
    }

    /**
     * Format multiple files
     */
    async function formatMultipleFiles(examType) {
        showLoading(true);

        try {
            const response = await fetch('/api/format-batch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    files: uploadedFiles.map(f => ({ name: f.name, content: f.content })),
                    exam_type: examType
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Batch formatting failed');
            }

            displayBatchResults(data.results, examType);

            const label = examType === 'practice' ? 'Practice Exam' : 'Final Exam';
            showToast(`Formatted ${data.results.length} files as ${label}!`, 'success');

        } catch (error) {
            console.error('Batch format error:', error);
            showToast(error.message || 'An error occurred', 'error');
        } finally {
            showLoading(false);
        }
    }

    /**
     * Download formatted file
     */
    async function downloadFile(text, format, examType) {
        showLoading(true);

        try {
            const response = await fetch(`/api/download/${format}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text, exam_type: examType }),
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.error || 'Download failed');
            }

            // Create download link
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            const typeLabel = examType === 'practice' ? 'practice' : 'final';
            a.download = `formatted_${typeLabel}_exam.${format}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();

            showToast(`Downloaded as ${format.toUpperCase()}!`, 'success');

        } catch (error) {
            console.error('Download error:', error);
            showToast(error.message || 'Download failed', 'error');
        } finally {
            showLoading(false);
        }
    }

    /**
     * Download batch of files as ZIP
     */
    async function downloadBatch(format, examType) {
        showLoading(true);

        try {
            const response = await fetch(`/api/download-batch/${format}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    files: uploadedFiles.map(f => ({ name: f.name, content: f.content })),
                    exam_type: examType
                }),
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.error || 'Batch download failed');
            }

            // Create download link for ZIP
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            const typeLabel = examType === 'practice' ? 'practice' : 'final';
            a.download = `formatted_${typeLabel}_exams.zip`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();

            showToast(`Downloaded ${uploadedFiles.length} files as ZIP!`, 'success');

        } catch (error) {
            console.error('Batch download error:', error);
            showToast(error.message || 'Batch download failed', 'error');
        } finally {
            showLoading(false);
        }
    }

    /**
     * Display batch results summary
     */
    function displayBatchResults(results, examType) {
        let totalQuestions = 0;
        let totalAnswers = 0;

        let html = '<div class="formatted-section">';
        html += '<div class="section-title">Batch Processing Results</div>';
        html += `<p style="color: var(--text-secondary); margin-bottom: 20px;">${results.length} files processed as ${examType === 'practice' ? 'Practice Exam' : 'Final Exam'}</p>`;

        results.forEach((result, index) => {
            const qCount = result.stats?.question_count || 0;
            const aCount = result.stats?.answer_count || 0;
            totalQuestions += qCount;
            totalAnswers += aCount;

            html += `
                <div class="file-result" style="padding: 12px; background: rgba(255,255,255,0.05); border-radius: 8px; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="color: var(--accent-cyan); font-weight: 500;">${escapeHtml(result.filename)}</span>
                        <span style="color: var(--text-muted); font-size: 0.85rem;">${qCount} questions, ${aCount} answers</span>
                    </div>
                    ${result.warning ? `<div style="color: var(--error-red); font-size: 0.8rem; margin-top: 5px;">${escapeHtml(result.warning)}</div>` : ''}
                </div>
            `;
        });

        html += '</div>';

        outputContent.innerHTML = html;
        qCount.textContent = totalQuestions;
        aCount.textContent = totalAnswers;
    }

    /**
     * Display formatted output in the right panel.
     */
    function displayFormattedOutput(data, examType) {
        const { questions, answers, title } = data;
        const examTitle = title || 'Exam';

        let html = '';

        // Questions section - same format for both exam types
        if (questions && questions.length > 0) {
            html += '<div class="formatted-section">';
            html += '<div class="doc-header">';
            html += `<div class="doc-header-title">${escapeHtml(examTitle)}</div>`;
            html += '<div class="doc-header-section">Questions</div>';
            html += '</div>';
            html += '<div class="document-preview">';

            questions.forEach(q => {
                // Question line: "#. <question text>"
                html += `<div class="doc-line question-line">`;
                html += `<span class="q-number">${q.number}.</span>`;
                html += `<span class="q-text">${escapeHtml(q.text)}</span>`;
                html += '</div>';

                // Blank line after question
                html += '<div class="doc-line blank"></div>';

                // Choices - each followed by a blank line
                if (q.choices && q.choices.length > 0) {
                    q.choices.forEach(c => {
                        html += `<div class="doc-line choice-line">`;
                        html += `<span class="choice-letter">${c.letter}.</span>`;
                        html += `<span class="choice-text">${escapeHtml(c.text)}</span>`;
                        html += '</div>';

                        // Blank line after EACH choice
                        html += '<div class="doc-line blank"></div>';
                    });
                }
            });

            html += '</div>';
            html += '</div>';
        }

        // Answer Key section - different format based on exam type
        if (answers && answers.length > 0) {
            html += '<div class="formatted-section answer-key-section">';
            html += '<div class="doc-header">';
            html += `<div class="doc-header-title">${escapeHtml(examTitle)}</div>`;
            html += '<div class="doc-header-section">Answer Key</div>';
            html += '</div>';
            html += '<div class="page-break-note">(Starts on new page in Word/PDF)</div>';
            html += '<div class="document-preview">';

            if (examType === 'practice') {
                // Practice exam answer format: "#.    <letter>    <code ref>"
                answers.forEach(a => {
                    html += `<div class="doc-line answer-line answer-practice">`;
                    html += `<span class="a-number">${a.number}.</span>`;
                    html += `<span class="a-letter-practice">${a.letter}</span>`;
                    html += `<span class="a-payload">${escapeHtml(a.payload)}</span>`;
                    html += '</div>';

                    // Blank line after each answer
                    html += '<div class="doc-line blank"></div>';
                });
            } else {
                // Final exam answer format: "#.    <letter>)    <source>    (<citation>)"
                answers.forEach(a => {
                    html += `<div class="doc-line answer-line answer-final">`;
                    html += `<span class="a-number">${a.number}.</span>`;
                    html += `<span class="a-letter">${a.letter})</span>`;
                    html += `<span class="a-payload">${escapeHtml(a.payload)}</span>`;
                    html += '</div>';

                    // Blank line after each answer
                    html += '<div class="doc-line blank"></div>';
                });
            }

            html += '</div>';
            html += '</div>';
        }

        // Empty state
        if (!html) {
            html = `
                <div class="placeholder-message">
                    <div class="placeholder-icon">
                        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="currentColor" stroke-width="2"/>
                            <path d="M12 16V12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                            <path d="M12 8H12.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                        </svg>
                    </div>
                    <p>No content found</p>
                    <span>Check your input format</span>
                </div>
            `;
        }

        outputContent.innerHTML = html;
    }

    /**
     * Update statistics display
     */
    function updateStats(stats) {
        if (stats) {
            qCount.textContent = stats.question_count || 0;
            aCount.textContent = stats.answer_count || 0;
        }
    }

    /**
     * Show/hide loading overlay
     */
    function showLoading(show) {
        if (show) {
            loadingOverlay.classList.add('visible');
        } else {
            loadingOverlay.classList.remove('visible');
        }
    }

    /**
     * Show toast notification
     */
    function showToast(message, type = 'info') {
        toast.textContent = message;
        toast.className = 'toast';
        toast.classList.add(type);

        // Show toast
        requestAnimationFrame(() => {
            toast.classList.add('visible');
        });

        // Hide after 3 seconds
        setTimeout(() => {
            toast.classList.remove('visible');
        }, 3000);
    }

    /**
     * Escape HTML to prevent XSS
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Add visual feedback on panel focus
    inputText.addEventListener('focus', () => {
        inputText.closest('.panel').style.borderColor = 'rgba(0, 212, 255, 0.5)';
    });

    inputText.addEventListener('blur', () => {
        inputText.closest('.panel').style.borderColor = '';
    });
});

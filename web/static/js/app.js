/**
 * AI FORMAT - LLM Output Formatter
 * Main Application JavaScript
 */

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const inputText = document.getElementById('input-text');
    const outputContent = document.getElementById('output-content');
    const formatBtn = document.getElementById('format-btn');
    const downloadButtons = document.getElementById('download-buttons');
    const charCount = document.getElementById('char-count');
    const qCount = document.getElementById('q-count');
    const aCount = document.getElementById('a-count');
    const loadingOverlay = document.getElementById('loading-overlay');
    const toast = document.getElementById('toast');

    // State
    let currentText = '';
    let formattedData = null;

    // Character count update
    inputText.addEventListener('input', () => {
        charCount.textContent = inputText.value.length.toLocaleString();
        currentText = inputText.value;
    });

    // Format button click
    formatBtn.addEventListener('click', async () => {
        const text = inputText.value.trim();

        if (!text) {
            showToast('Please enter some text to format', 'error');
            return;
        }

        await formatText(text);
    });

    // Download button clicks
    downloadButtons.querySelectorAll('.download-button').forEach(btn => {
        btn.addEventListener('click', async () => {
            const format = btn.dataset.format;
            const text = inputText.value.trim();

            if (!text) {
                showToast('Please enter some text first', 'error');
                return;
            }

            await downloadFile(text, format);
        });
    });

    // Keyboard shortcut (Ctrl/Cmd + Enter to format)
    inputText.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            formatBtn.click();
        }
    });

    /**
     * Format the input text
     */
    async function formatText(text) {
        showLoading(true);

        try {
            const response = await fetch('/api/format', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Formatting failed');
            }

            formattedData = data;
            displayFormattedOutput(data);
            updateStats(data.stats);
            downloadButtons.classList.add('visible');
            showToast('Formatted successfully!', 'success');

        } catch (error) {
            console.error('Format error:', error);
            showToast(error.message || 'An error occurred', 'error');
        } finally {
            showLoading(false);
        }
    }

    /**
     * Download formatted file
     */
    async function downloadFile(text, format) {
        showLoading(true);

        try {
            const response = await fetch(`/api/download/${format}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text }),
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
            a.download = `formatted_exam.${format}`;
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
     * Display formatted output in the right panel
     * Matches VBA macro format exactly:
     * - Questions: "#.    <question>" with blank line after
     * - Choices: indented "A.    <choice>"
     * - Answers: "#.    A)    <source> Answer/Citation: <citation>"
     */
    function displayFormattedOutput(data) {
        const { questions, answers } = data;

        let html = '';

        // Questions section - formatted exactly like VBA output
        if (questions && questions.length > 0) {
            html += '<div class="formatted-section">';
            html += '<div class="section-title">QUESTIONS</div>';
            html += '<div class="formatted-content">';

            questions.forEach(q => {
                // Question line: "#.    <question text>"
                html += `<div class="format-line question-line">`;
                html += `<span class="line-number">${q.number}.</span>`;
                html += `<span class="line-tab"></span>`;
                html += `<span class="line-text">${escapeHtml(q.text)}</span>`;
                html += '</div>';

                // Blank line after question
                html += '<div class="format-line blank-line"></div>';

                // Choices - indented
                if (q.choices && q.choices.length > 0) {
                    q.choices.forEach(c => {
                        html += `<div class="format-line choice-line">`;
                        html += `<span class="choice-indent"></span>`;
                        html += `<span class="choice-letter">${c.letter}.</span>`;
                        html += `<span class="line-tab"></span>`;
                        html += `<span class="line-text">${escapeHtml(c.text)}</span>`;
                        html += '</div>';
                    });
                }

                // Blank line after choices (between questions)
                html += '<div class="format-line blank-line"></div>';
            });

            html += '</div>';
            html += '</div>';
        }

        // Answer Key section - formatted exactly like VBA output
        if (answers && answers.length > 0) {
            html += '<div class="formatted-section answer-section">';
            html += '<div class="section-title">ANSWER KEY</div>';
            html += '<div class="section-note">(Starts on new page in document)</div>';
            html += '<div class="formatted-content">';

            answers.forEach(a => {
                // Answer line: "#.    A)    <payload>"
                html += `<div class="format-line answer-line">`;
                html += `<span class="line-number">${a.number}.</span>`;
                html += `<span class="line-tab"></span>`;
                html += `<span class="answer-letter-box">${a.letter})</span>`;
                html += `<span class="line-tab"></span>`;
                html += `<span class="line-text">${escapeHtml(a.payload)}</span>`;
                html += '</div>';

                // Blank line after each answer
                html += '<div class="format-line blank-line"></div>';
            });

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

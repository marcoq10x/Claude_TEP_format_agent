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

    // State
    let currentText = '';
    let currentExamType = null;
    let formattedData = null;

    // Character count update
    inputText.addEventListener('input', () => {
        charCount.textContent = inputText.value.length.toLocaleString();
        currentText = inputText.value;
    });

    // Practice Exam button click
    practiceBtn.addEventListener('click', async () => {
        const text = inputText.value.trim();
        if (!text) {
            showToast('Please enter some text to format', 'error');
            return;
        }
        currentExamType = 'practice';
        await formatText(text, 'practice');
    });

    // Final Exam button click
    finalBtn.addEventListener('click', async () => {
        const text = inputText.value.trim();
        if (!text) {
            showToast('Please enter some text to format', 'error');
            return;
        }
        currentExamType = 'final';
        await formatText(text, 'final');
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

            if (!currentExamType) {
                showToast('Please format the text first using Practice or Final Exam', 'error');
                return;
            }

            await downloadFile(text, format, currentExamType);
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
            downloadButtons.classList.add('visible');

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
     * Display formatted output in the right panel.
     *
     * Both exam types use the same question format:
     * #. <question text>
     * <blank line>
     * A. <choice>
     * <blank line>
     * B. <choice>
     * <blank line>
     * C. <choice>
     * <blank line>
     * D. <choice>
     * <blank line>
     *
     * PRACTICE EXAM answer key:
     * #.    <letter>    <code reference>
     *
     * FINAL EXAM answer key:
     * #.    <letter>)    <source>    (<citation>)
     */
    function displayFormattedOutput(data, examType) {
        const { questions, answers } = data;

        let html = '';
        const typeLabel = examType === 'practice' ? 'PRACTICE EXAM' : 'FINAL EXAM';

        // Questions section - same format for both exam types
        if (questions && questions.length > 0) {
            html += '<div class="formatted-section">';
            html += `<div class="section-header">${typeLabel} - QUESTIONS</div>`;
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
            html += `<div class="section-header">${typeLabel} - ANSWER KEY</div>`;
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

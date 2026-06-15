// Course Creation App - Frontend JavaScript

const API_BASE = '';

// Store for streaming content
let streamingContent = '';

async function generateCourse() {
    const topicInput = document.getElementById('topic');
    const topic = topicInput.value.trim();

    if (!topic) {
        alert('请输入课程主题');
        return;
    }

    // Show progress section
    const progressSection = document.getElementById('progressSection');
    const resultSection = document.getElementById('resultSection');
    const errorSection = document.getElementById('errorSection');
    const progressLog = document.getElementById('progressLog');
    const courseContent = document.getElementById('courseContent');
    const generateBtn = document.getElementById('generateBtn');

    // Reset UI
    progressSection.classList.remove('hidden');
    resultSection.classList.add('hidden');
    errorSection.classList.add('hidden');
    progressLog.innerHTML = '';
    courseContent.innerHTML = '';
    generateBtn.disabled = true;
    generateBtn.textContent = '生成中...';
    streamingContent = '';

    try {
        // Make SSE request
        const response = await fetch(`${API_BASE}/api/chat_stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: topic,
                user_id: 'web_user',
            }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error: ${response.status}`);
        }

        // Read SSE stream
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });

            // Process complete lines
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (line.trim()) {
                    try {
                        const event = JSON.parse(line);
                        handleEvent(event, progressLog, courseContent, resultSection);
                    } catch (e) {
                        console.error('Parse error:', e, line);
                    }
                }
            }
        }

        // Process remaining buffer
        if (buffer.trim()) {
            try {
                const event = JSON.parse(buffer);
                handleEvent(event, progressLog, courseContent, resultSection);
            } catch (e) {
                console.error('Parse error:', e, buffer);
            }
        }

    } catch (error) {
        errorSection.classList.remove('hidden');
        document.getElementById('errorMessage').textContent = error.message;
        progressSection.classList.add('hidden');
    }

    // Reset button
    generateBtn.disabled = false;
    generateBtn.textContent = '生成课程';
}

function handleEvent(event, progressLog, courseContent, resultSection) {
    if (event.type === 'progress') {
        // Add progress message
        const agentEmoji = getAgentEmoji(event.agent);
        const progressItem = document.createElement('div');
        progressItem.className = 'progress-item';
        progressItem.innerHTML = `<span class="agent">${agentEmoji} ${event.agent}</span>: ${event.message}`;
        progressLog.appendChild(progressItem);
    } else if (event.type === 'chunk') {
        // Streaming content chunk - show result section and append content
        resultSection.classList.remove('hidden');
        streamingContent += event.content || '';
        courseContent.innerHTML = renderMarkdown(streamingContent);
        // Auto-scroll to bottom
        courseContent.scrollTop = courseContent.scrollHeight;
    } else if (event.type === 'result') {
        // Final result - update with complete content
        resultSection.classList.remove('hidden');
        if (event.course) {
            streamingContent = event.course;
            courseContent.innerHTML = renderMarkdown(event.course);
        }
    } else if (event.type === 'error') {
        // Show error
        document.getElementById('errorSection').classList.remove('hidden');
        document.getElementById('errorMessage').textContent = event.error;
    }
}

function getAgentEmoji(agent) {
    const emojis = {
        'researcher': '🔍',
        'judge': '⚖️',
        'content_builder': '✍️',
    };
    return emojis[agent] || '🤖';
}

function renderMarkdown(text) {
    // Use marked.js for proper Markdown rendering
    if (typeof marked !== 'undefined') {
        marked.setOptions({
            breaks: true,
            gfm: true,
        });
        return marked.parse(text);
    }
    // Fallback: simple rendering
    let html = text;
    html = html.replace(/^### (.*)$/gm, '<h3>$1</h3>');
    html = html.replace(/^## (.*)$/gm, '<h2>$1</h2>');
    html = html.replace(/^# (.*)$/gm, '<h1>$1</h1>');
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/^- (.*)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');
    html = html.replace(/\n\n/g, '</p><p>');
    html = '<p>' + html + '</p>';
    html = html.replace(/<p>\s*<\/p>/g, '');
    html = html.replace(/<p>\s*<(h[1-6]|ul|li)/g, '$1');
    html = html.replace(/<\/(h[1-6]|ul|li)>\s*<\/p>/g, '</$1>');
    return html;
}

function copyContent() {
    const content = document.getElementById('courseContent').innerText;
    navigator.clipboard.writeText(content).then(() => {
        alert('内容已复制到剪贴板');
    }).catch(err => {
        console.error('Copy failed:', err);
    });
}
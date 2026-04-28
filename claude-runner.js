const { spawn } = require('child_process');

const CLAUDE_BIN = process.env.CLAUDE_BIN || 'claude';
const WORK_DIR = process.env.WORK_DIR || process.cwd();
const TIMEOUT_MS = parseInt(process.env.CLAUDE_TIMEOUT_MS || '300000', 10);

const TOOL_LABELS = {
  Bash: '🖥 Bash',
  Edit: '✏️ Edit',
  Write: '📝 Write',
  Read: '📖 Read',
  TodoWrite: '📋 Todo',
  WebFetch: '🌐 Fetch',
  WebSearch: '🔍 Search',
  Glob: '🗂 Glob',
  Grep: '🔎 Grep',
  LS: '📁 LS',
};

function toolLabel(name) {
  return TOOL_LABELS[name] || ('🔧 ' + name);
}

function runClaude(prompt, { onChunk, onTool, sessionId } = {}) {
  return new Promise((resolve, reject) => {
    const args = [
      '--print',
      '--output-format', 'stream-json',
      '--dangerously-skip-permissions',
    ];
    if (sessionId) args.push('--resume', sessionId);
    args.push(prompt);

    const proc = spawn(CLAUDE_BIN, args, {
      cwd: WORK_DIR,
      env: process.env,
    });

    let fullText = '';
    let newSessionId = sessionId || null;
    let buffer = '';
    let timedOut = false;
    const toolsUsed = [];

    const timeout = setTimeout(() => {
      timedOut = true;
      proc.kill('SIGTERM');
      reject(new Error('Claude timed out after ' + TIMEOUT_MS / 1000 + 's'));
    }, TIMEOUT_MS);

    proc.stdout.on('data', (data) => {
      buffer += data.toString();
      const lines = buffer.split('\n');
      buffer = lines.pop();

      for (const line of lines) {
        if (!line.trim()) continue;
        let event;
        try { event = JSON.parse(line); } catch { continue; }

        if (event.type === 'session_id') {
          newSessionId = event.session_id;
        }

        if (event.type === 'assistant') {
          const content = event.message && event.message.content ? event.message.content : [];
          for (const block of content) {
            if (block.type === 'text') {
              fullText += block.text;
              if (onChunk) onChunk(block.text);
            }
            if (block.type === 'tool_use') {
              const label = toolLabel(block.name);
              let detail = '';
              if (block.name === 'Bash' && block.input && block.input.command) {
                detail = block.input.command.slice(0, 60);
              } else if ((block.name === 'Edit' || block.name === 'Write' || block.name === 'Read') && block.input && block.input.file_path) {
                detail = block.input.file_path;
              } else if (block.name === 'WebSearch' && block.input && block.input.query) {
                detail = block.input.query.slice(0, 60);
              } else if (block.name === 'WebFetch' && block.input && block.input.url) {
                detail = block.input.url.slice(0, 60);
              }
              const toolInfo = { label, detail, name: block.name };
              toolsUsed.push(toolInfo);
              if (onTool) onTool(toolInfo);
            }
          }
        }
      }
    });

    proc.stderr.on('data', () => {});

    proc.on('close', (code) => {
      clearTimeout(timeout);
      if (timedOut) return;
      resolve({
        text: fullText || '(no text response)',
        sessionId: newSessionId,
        toolsUsed,
      });
    });

    proc.on('error', (err) => {
      clearTimeout(timeout);
      reject(err);
    });
  });
}

module.exports = { runClaude };

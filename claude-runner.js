const { spawn } = require('child_process');
const path = require('path');

const CLAUDE_BIN = process.env.CLAUDE_BIN || 'claude';
const WORK_DIR = process.env.WORK_DIR || process.cwd();
const TIMEOUT_MS = parseInt(process.env.CLAUDE_TIMEOUT_MS || '300000', 10);

/**
 * Run Claude Code with a prompt in non-interactive mode.
 * Calls onChunk(text) with incremental text as it arrives.
 * Returns the full response text on completion.
 */
function runClaude(prompt, { onChunk, sessionId } = {}) {
  return new Promise((resolve, reject) => {
    const args = [
      '--print',
      '--output-format', 'stream-json',
      '--dangerously-skip-permissions',
    ];

    // Continue previous session if provided
    if (sessionId) {
      args.push('--resume', sessionId);
    }

    args.push(prompt);

    const proc = spawn(CLAUDE_BIN, args, {
      cwd: WORK_DIR,
      env: process.env,
    });

    let fullText = '';
    let newSessionId = sessionId || null;
    let buffer = '';
    let timedOut = false;

    const timeout = setTimeout(() => {
      timedOut = true;
      proc.kill('SIGTERM');
      reject(new Error('Claude timed out after ' + TIMEOUT_MS / 1000 + 's'));
    }, TIMEOUT_MS);

    proc.stdout.on('data', (data) => {
      buffer += data.toString();
      const lines = buffer.split('\n');
      buffer = lines.pop(); // keep incomplete line

      for (const line of lines) {
        if (!line.trim()) continue;
        let event;
        try {
          event = JSON.parse(line);
        } catch {
          continue;
        }

        // stream-json emits {type, ...} events
        if (event.type === 'session_id') {
          newSessionId = event.session_id;
        }

        if (event.type === 'assistant') {
          // content blocks inside assistant message
          const content = event.message?.content || [];
          for (const block of content) {
            if (block.type === 'text') {
              fullText += block.text;
              if (onChunk) onChunk(block.text);
            }
          }
        }

        // tool_use result text (tool output summary)
        if (event.type === 'tool_result') {
          const text = event.content?.find(c => c.type === 'text')?.text;
          if (text && onChunk) {
            onChunk('\n`' + text.slice(0, 200) + (text.length > 200 ? '…`' : '`'));
          }
        }
      }
    });

    proc.stderr.on('data', (data) => {
      // stderr is Claude's own debug/status output, ignore unless debug needed
    });

    proc.on('close', (code) => {
      clearTimeout(timeout);
      if (timedOut) return;
      if (code !== 0 && !fullText) {
        reject(new Error(`Claude exited with code ${code}`));
        return;
      }
      resolve({ text: fullText || '(no text response)', sessionId: newSessionId });
    });

    proc.on('error', (err) => {
      clearTimeout(timeout);
      reject(err);
    });
  });
}

module.exports = { runClaude };

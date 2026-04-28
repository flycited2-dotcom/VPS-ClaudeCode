#!/usr/bin/env python3
"""
Run this on the VPS:  python3 deploy.py
It rewrites bot.js and claude-runner.js with the correct versions.
"""
import os

BASE = '/home/user/VPS-ClaudeCode'
os.makedirs(BASE, exist_ok=True)

# ── claude-runner.js ──────────────────────────────────────────────────────────
runner = r"""const { spawn } = require('child_process');

const CLAUDE_BIN = process.env.CLAUDE_BIN || 'claude';
const WORK_DIR = process.env.WORK_DIR || process.cwd();
const TIMEOUT_MS = parseInt(process.env.CLAUDE_TIMEOUT_MS || '300000', 10);

const TOOL_LABELS = {
  Bash: '🖥 Bash', Edit: '✏️ Edit', Write: '📝 Write', Read: '📖 Read',
  TodoWrite: '📋 Todo', WebFetch: '🌐 Fetch', WebSearch: '🔍 Search',
  Glob: '🗂 Glob', Grep: '🔎 Grep', LS: '📁 LS',
};

function toolLabel(name) { return TOOL_LABELS[name] || ('🔧 ' + name); }

function runClaude(prompt, { onChunk, onTool, sessionId } = {}) {
  return new Promise((resolve, reject) => {
    const args = ['--print', '--output-format', 'stream-json', '--dangerously-skip-permissions'];
    if (sessionId) args.push('--resume', sessionId);
    args.push(prompt);

    const proc = spawn(CLAUDE_BIN, args, { cwd: WORK_DIR, env: process.env });
    let fullText = '', newSessionId = sessionId || null, buffer = '', timedOut = false;
    const toolsUsed = [];

    const timeout = setTimeout(() => {
      timedOut = true; proc.kill('SIGTERM');
      reject(new Error('Claude timed out after ' + TIMEOUT_MS / 1000 + 's'));
    }, TIMEOUT_MS);

    proc.stdout.on('data', (data) => {
      buffer += data.toString();
      const lines = buffer.split('\n'); buffer = lines.pop();
      for (const line of lines) {
        if (!line.trim()) continue;
        let event; try { event = JSON.parse(line); } catch { continue; }
        if (event.type === 'session_id') newSessionId = event.session_id;
        if (event.type === 'assistant') {
          const content = (event.message && event.message.content) ? event.message.content : [];
          for (const block of content) {
            if (block.type === 'text') { fullText += block.text; if (onChunk) onChunk(block.text); }
            if (block.type === 'tool_use') {
              const label = toolLabel(block.name);
              let detail = '';
              if (block.name === 'Bash' && block.input && block.input.command) detail = block.input.command.slice(0, 60);
              else if (['Edit','Write','Read'].includes(block.name) && block.input && block.input.file_path) detail = block.input.file_path;
              else if (block.name === 'WebSearch' && block.input && block.input.query) detail = block.input.query.slice(0, 60);
              else if (block.name === 'WebFetch' && block.input && block.input.url) detail = block.input.url.slice(0, 60);
              const toolInfo = { label, detail, name: block.name };
              toolsUsed.push(toolInfo);
              if (onTool) onTool(toolInfo);
            }
          }
        }
      }
    });

    proc.stderr.on('data', () => {});
    proc.on('close', () => { clearTimeout(timeout); if (!timedOut) resolve({ text: fullText || '(no text response)', sessionId: newSessionId, toolsUsed }); });
    proc.on('error', (err) => { clearTimeout(timeout); reject(err); });
  });
}

module.exports = { runClaude };
"""

# ── bot.js ────────────────────────────────────────────────────────────────────
bot = r"""require('dotenv').config();
const { Bot } = require('grammy');
const { runClaude } = require('./claude-runner');
const { execSync } = require('child_process');
const fs = require('fs');
const https = require('https');

const TOKEN = process.env.TELEGRAM_BOT_TOKEN;
const ALLOWED_IDS = (process.env.ALLOWED_USER_IDS || '').split(',').map(s => s.trim()).filter(Boolean).map(Number);
const UPDATE_INTERVAL = parseInt(process.env.STREAM_UPDATE_INTERVAL_MS || '2000', 10);
const WORK_DIR = process.env.WORK_DIR || process.cwd();
const OPENAI_API_KEY = process.env.OPENAI_API_KEY || '';

if (!TOKEN) { console.error('TELEGRAM_BOT_TOKEN not set'); process.exit(1); }

const bot = new Bot(TOKEN);
const sessions = new Map();
const inFlight = new Map();

function isAllowed(id) { return ALLOWED_IDS.length === 0 || ALLOWED_IDS.includes(id); }
function splitText(text, maxLen) { const p = []; let i = 0; while (i < text.length) { p.push(text.slice(i, i + maxLen)); i += maxLen; } return p; }
function safeEdit(ctx, chatId, msgId, text) { return ctx.api.editMessageText(chatId, msgId, text || '...').catch(() => {}); }

function downloadFile(url, dest) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(dest);
    https.get(url, res => { res.pipe(file); file.on('finish', () => { file.close(); resolve(); }); }).on('error', reject);
  });
}

async function transcribeVoice(filePath) {
  if (!OPENAI_API_KEY) throw new Error('OPENAI_API_KEY не настроен в .env');
  const FormData = require('form-data');
  const form = new FormData();
  form.append('file', fs.createReadStream(filePath), { filename: 'voice.ogg', contentType: 'audio/ogg' });
  form.append('model', 'whisper-1');
  form.append('language', 'ru');
  return new Promise((resolve, reject) => {
    const req = https.request({ hostname: 'api.openai.com', path: '/v1/audio/transcriptions', method: 'POST', headers: { ...form.getHeaders(), Authorization: 'Bearer ' + OPENAI_API_KEY } }, res => {
      let data = ''; res.on('data', c => { data += c; }); res.on('end', () => { try { const j = JSON.parse(data); if (j.text) resolve(j.text); else reject(new Error((j.error && j.error.message) || 'Whisper error')); } catch { reject(new Error('Whisper parse error')); } });
    });
    req.on('error', reject); form.pipe(req);
  });
}

bot.command('start', ctx => ctx.reply(
  'Claude Code Bridge\n\nОтправь задачу текстом или голосом — выполню на VPS.\n\n' +
  '/reset  — новая сессия\n/status — ID сессии\n/cancel — отменить задачу\n/logs   — логи бота\n/files  — изменённые файлы\n/where  — рабочая папка'
));
bot.command('reset', ctx => { sessions.delete(ctx.chat.id); return ctx.reply('Сессия сброшена.'); });
bot.command('status', ctx => { const s = sessions.get(ctx.chat.id); return ctx.reply(s ? 'Сессия: ' + s : 'Нет активной сессии.'); });
bot.command('cancel', ctx => {
  if (inFlight.get(ctx.chat.id) === 'running') { inFlight.set(ctx.chat.id, 'cancelled'); return ctx.reply('Отмена запрошена.'); }
  return ctx.reply('Нет активных задач.');
});
bot.command('where', ctx => ctx.reply('Рабочая папка: ' + WORK_DIR));
bot.command('logs', async ctx => {
  try {
    const out = execSync('pm2 logs claude-telegram-bridge --lines 30 --nostream 2>&1 || tail -30 /root/.pm2/logs/claude-telegram-bridge-out.log 2>/dev/null', { encoding: 'utf8' }).slice(-3500);
    await ctx.reply(out || 'Логи пусты.');
  } catch (e) { await ctx.reply('Ошибка: ' + e.message); }
});
bot.command('files', async ctx => {
  try {
    const out = execSync('find ' + WORK_DIR + ' -newer ' + WORK_DIR + '/package.json -type f -not -path "*/node_modules/*" -not -path "*/.git/*" 2>/dev/null | head -20', { encoding: 'utf8' });
    await ctx.reply(out.trim() || 'Изменённых файлов нет.');
  } catch (e) { await ctx.reply('Ошибка: ' + e.message); }
});

bot.on('message:voice', async ctx => {
  if (!isAllowed(ctx.from && ctx.from.id)) return ctx.reply('Access denied.');
  const statusMsg = await ctx.reply('Распознаю голос...');
  const chatId = ctx.chat.id;
  const msgId = statusMsg.message_id;
  try {
    const fileInfo = await ctx.api.getFile(ctx.message.voice.file_id);
    const url = 'https://api.telegram.org/file/bot' + TOKEN + '/' + fileInfo.file_path;
    const tmp = '/tmp/voice_' + Date.now() + '.ogg';
    await downloadFile(url, tmp);
    const text = await transcribeVoice(tmp);
    fs.unlinkSync(tmp);
    await safeEdit(ctx, chatId, msgId, 'Вы сказали: ' + text + '\n\nВыполняю...');
    await processTask(ctx, chatId, msgId, text);
  } catch (err) {
    await safeEdit(ctx, chatId, msgId, 'Голос: ' + err.message);
  }
});

bot.on('message:text', async ctx => {
  if (!isAllowed(ctx.from && ctx.from.id)) return ctx.reply('Access denied.');
  const chatId = ctx.chat.id;
  if (inFlight.get(chatId) === 'running') return ctx.reply('Задача уже выполняется. /cancel для остановки.');
  const statusMsg = await ctx.reply('Выполняю...');
  await processTask(ctx, chatId, statusMsg.message_id, ctx.message.text.trim());
});

async function processTask(ctx, chatId, msgId, prompt) {
  inFlight.set(chatId, 'running');
  let accumulated = '', lastEdit = 0, toolStatus = '';
  const flush = async (final) => {
    if (!accumulated && !final) return;
    if (!final && Date.now() - lastEdit < UPDATE_INTERVAL) return;
    lastEdit = Date.now();
    const body = accumulated.slice(-3600);
    const indicator = final ? '' : (toolStatus ? '\n\n' + toolStatus + '\n...' : '\n\nДумаю...');
    await safeEdit(ctx, chatId, msgId, body + indicator);
  };
  try {
    const { text: result, sessionId: newSid, toolsUsed } = await runClaude(prompt, {
      sessionId: sessions.get(chatId),
      onChunk: async chunk => { if (inFlight.get(chatId) === 'cancelled') return; accumulated += chunk; toolStatus = ''; await flush(false); },
      onTool: async tool => { if (inFlight.get(chatId) === 'cancelled') return; toolStatus = tool.label + (tool.detail ? ': ' + tool.detail : ''); await flush(false); },
    });
    if (newSid) sessions.set(chatId, newSid);
    if (!accumulated) accumulated = result;
    if (toolsUsed && toolsUsed.length > 0) {
      accumulated += '\n\n─────\nИспользовано: ' + toolsUsed.map(t => t.label + (t.detail ? ' ' + t.detail.slice(0, 30) : '')).join(', ');
    }
    if (accumulated.length > 4000) {
      const parts = splitText(accumulated, 4000);
      await safeEdit(ctx, chatId, msgId, parts[0]);
      for (let i = 1; i < parts.length; i++) await ctx.reply(parts[i]);
    } else { await safeEdit(ctx, chatId, msgId, accumulated); }
  } catch (err) {
    await safeEdit(ctx, chatId, msgId, 'Ошибка: ' + ((err && err.message) || String(err)));
  } finally { inFlight.delete(chatId); }
}

bot.catch(err => console.error('Bot error:', err.message));
bot.start();
console.log('Claude Code Telegram bridge started.');
console.log('Work dir:', WORK_DIR);
console.log('Allowed IDs:', ALLOWED_IDS.length ? ALLOWED_IDS.join(', ') : 'ALL');
console.log('Voice:', OPENAI_API_KEY ? 'enabled' : 'disabled');
"""

# ── .env (preserve existing token if present) ────────────────────────────────
env_path = os.path.join(BASE, '.env')
if not os.path.exists(env_path):
    env_content = """TELEGRAM_BOT_TOKEN=8766937307:AAGm1YC9VWsVLH-_hlDDdj8WSLqyynXvGFA
ALLOWED_USER_IDS=1264067528
WORK_DIR=/home/user/VPS-ClaudeCode
CLAUDE_BIN=
CLAUDE_TIMEOUT_MS=300000
STREAM_UPDATE_INTERVAL_MS=2000
OPENAI_API_KEY=
"""
    with open(env_path, 'w') as f:
        f.write(env_content)
    print('.env created')
else:
    # Add OPENAI_API_KEY if missing
    with open(env_path, 'r') as f:
        content = f.read()
    if 'OPENAI_API_KEY' not in content:
        with open(env_path, 'a') as f:
            f.write('\nOPENAI_API_KEY=\n')
        print('.env updated (added OPENAI_API_KEY)')
    else:
        print('.env already exists, skipped')

with open(os.path.join(BASE, 'claude-runner.js'), 'w') as f:
    f.write(runner)
print('claude-runner.js written')

with open(os.path.join(BASE, 'bot.js'), 'w') as f:
    f.write(bot)
print('bot.js written')

print('\nDone! Now run:')
print('  cd /home/user/VPS-ClaudeCode && npm install && pm2 restart claude-telegram-bridge')

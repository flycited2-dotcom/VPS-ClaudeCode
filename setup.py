#!/usr/bin/env python3
"""
Универсальный установщик Claude Code Telegram Bridge.
Запускать на сервере: python3 setup.py
"""
import os, sys, subprocess, base64, json

BASE = '/home/user/VPS-ClaudeCode'

# ── Утилиты ───────────────────────────────────────────────────────────────────

def run(cmd, check=True, capture=False):
    kw = dict(shell=True, text=True)
    if capture:
        kw['capture_output'] = True
    r = subprocess.run(cmd, **kw)
    if check and r.returncode != 0:
        print(f'  ОШИБКА: {cmd}')
        if capture:
            print(r.stderr)
    return r

def write(path, content):
    with open(path, 'w') as f:
        f.write(content)
    print(f'  Создан: {path}')

def header(msg):
    print(f'\n{"─"*50}\n  {msg}\n{"─"*50}')

# ── Шаг 1: Проверка окружения ─────────────────────────────────────────────────

header('1. Проверка окружения')

node = run('node --version', capture=True)
print(f'  Node.js: {node.stdout.strip()}')

npm_r = run('npm --version', capture=True)
print(f'  npm:     {npm_r.stdout.strip()}')

# Найти claude
claude_bin = ''
for p in ['/opt/node22/bin/claude', '/usr/local/bin/claude', '/usr/bin/claude']:
    if os.path.exists(p):
        claude_bin = p
        break
if not claude_bin:
    r = run('which claude', capture=True, check=False)
    if r.returncode == 0:
        claude_bin = r.stdout.strip()

if claude_bin:
    ver = run(f'{claude_bin} --version', capture=True)
    print(f'  Claude:  {ver.stdout.strip()} ({claude_bin})')
else:
    print('  Claude:  НЕ НАЙДЕН — проверь установку')

# Проверить авторизацию Claude (OAuth или API ключ)
api_key = os.environ.get('ANTHROPIC_API_KEY', '')
oauth_ok = False
oauth_files = ['/root/.claude/settings.json', '/root/.claude/.credentials.json',
               '/root/.config/claude/settings.json']
for f in oauth_files:
    if os.path.exists(f):
        oauth_ok = True
        break

if api_key:
    print(f'  Авторизация: API ключ (ANTHROPIC_API_KEY)')
elif oauth_ok:
    print(f'  Авторизация: OAuth сессия (claude.ai) — работает без API ключа')
else:
    print(f'  Авторизация: НЕ НАЙДЕНА!')
    print(f'  Запусти вручную: {claude_bin or "claude"} — войди через браузер, затем повтори setup.py')

# ── Шаг 2: Создать папку и package.json ──────────────────────────────────────

header('2. Создание папки проекта')
os.makedirs(BASE, exist_ok=True)
print(f'  Папка: {BASE}')

pkg = {
    "name": "vps-claude-telegram-bridge",
    "version": "1.0.0",
    "main": "bot.js",
    "type": "commonjs",
    "scripts": {"start": "node bot.js"},
    "dependencies": {
        "dotenv": "^16.4.5",
        "grammy": "^1.42.0",
        "form-data": "^4.0.0"
    }
}
write(os.path.join(BASE, 'package.json'), json.dumps(pkg, indent=2))

# ── Шаг 3: .env ──────────────────────────────────────────────────────────────

header('3. Настройка .env')
env_path = os.path.join(BASE, '.env')
existing = {}
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                k, v = line.strip().split('=', 1)
                existing[k] = v

defaults = {
    'TELEGRAM_BOT_TOKEN': '8766937307:AAGm1YC9VWsVLH-_hlDDdj8WSLqyynXvGFA',
    'ALLOWED_USER_IDS': '1264067528',
    'WORK_DIR': BASE,
    'CLAUDE_BIN': claude_bin,
    'CLAUDE_TIMEOUT_MS': '300000',
    'STREAM_UPDATE_INTERVAL_MS': '2000',
    'OPENAI_API_KEY': '',
    # ANTHROPIC_API_KEY не добавляем — Claude Code использует OAuth из ~/.claude/
}
for k, v in defaults.items():
    if k not in existing:
        existing[k] = v

env_content = '\n'.join(f'{k}={v}' for k, v in existing.items()) + '\n'
write(env_path, env_content)
print(f'  Токен бота: настроен')
print(f'  Allowed user: 1264067528')
print(f'  Claude bin: {claude_bin or "auto-detect"}')

# ── Шаг 4: claude-runner.js ───────────────────────────────────────────────────

header('4. Создание claude-runner.js')

runner_js = r"""const { spawn } = require('child_process');

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
    const args = [
      '--print',
      '--output-format', 'stream-json',
      '--dangerously-skip-permissions',
      '--append-system-prompt', 'Всегда отвечай на русском языке.',
    ];
    if (sessionId) args.push('--resume', sessionId);
    args.push(prompt);

    const proc = spawn(CLAUDE_BIN, args, { cwd: WORK_DIR, env: process.env });
    let fullText = '', newSessionId = sessionId || null, buffer = '', timedOut = false;
    const toolsUsed = [];

    const timeout = setTimeout(() => {
      timedOut = true; proc.kill('SIGTERM');
      reject(new Error('Claude не ответил за ' + TIMEOUT_MS / 1000 + ' сек'));
    }, TIMEOUT_MS);

    proc.stdout.on('data', (data) => {
      buffer += data.toString();
      const lines = buffer.split('\n'); buffer = lines.pop();
      for (const line of lines) {
        if (!line.trim()) continue;
        let event; try { event = JSON.parse(line); } catch { continue; }
        if (event.type === 'session_id') newSessionId = event.session_id;
        if (event.type === 'assistant') {
          const content = (event.message && event.message.content) || [];
          for (const block of content) {
            if (block.type === 'text') {
              fullText += block.text;
              if (onChunk) onChunk(block.text);
            }
            if (block.type === 'tool_use') {
              const label = toolLabel(block.name);
              let detail = '';
              if (block.name === 'Bash' && block.input && block.input.command)
                detail = block.input.command.slice(0, 60);
              else if (['Edit','Write','Read'].includes(block.name) && block.input && block.input.file_path)
                detail = block.input.file_path;
              else if (block.name === 'WebSearch' && block.input && block.input.query)
                detail = block.input.query.slice(0, 60);
              const toolInfo = { label, detail, name: block.name };
              toolsUsed.push(toolInfo);
              if (onTool) onTool(toolInfo);
            }
          }
        }
      }
    });

    proc.stderr.on('data', () => {});
    proc.on('close', () => {
      clearTimeout(timeout);
      if (!timedOut) resolve({ text: fullText || '(нет ответа)', sessionId: newSessionId, toolsUsed });
    });
    proc.on('error', (err) => { clearTimeout(timeout); reject(err); });
  });
}

module.exports = { runClaude };
"""
write(os.path.join(BASE, 'claude-runner.js'), runner_js)

# ── Шаг 5: bot.js ─────────────────────────────────────────────────────────────

header('5. Создание bot.js')

bot_js = r"""require('dotenv').config();
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

if (!TOKEN) { console.error('TELEGRAM_BOT_TOKEN не указан в .env'); process.exit(1); }

const bot = new Bot(TOKEN);
const sessions = new Map();
const inFlight = new Map();

function isAllowed(id) { return ALLOWED_IDS.length === 0 || ALLOWED_IDS.includes(id); }

function splitText(text, maxLen) {
  const parts = []; let i = 0;
  while (i < text.length) { parts.push(text.slice(i, i + maxLen)); i += maxLen; }
  return parts;
}

function safeEdit(ctx, chatId, msgId, text) {
  return ctx.api.editMessageText(chatId, msgId, text || '…').catch(() => {});
}

function downloadFile(url, dest) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(dest);
    https.get(url, res => { res.pipe(file); file.on('finish', () => { file.close(); resolve(); }); }).on('error', reject);
  });
}

async function transcribeVoice(filePath) {
  if (!OPENAI_API_KEY) throw new Error('Добавь OPENAI_API_KEY в .env для голосовых сообщений');
  const FormData = require('form-data');
  const form = new FormData();
  form.append('file', fs.createReadStream(filePath), { filename: 'voice.ogg', contentType: 'audio/ogg' });
  form.append('model', 'whisper-1');
  form.append('language', 'ru');
  return new Promise((resolve, reject) => {
    const req = https.request({
      hostname: 'api.openai.com', path: '/v1/audio/transcriptions', method: 'POST',
      headers: { ...form.getHeaders(), Authorization: 'Bearer ' + OPENAI_API_KEY },
    }, res => {
      let data = '';
      res.on('data', c => { data += c; });
      res.on('end', () => {
        try { const j = JSON.parse(data); if (j.text) resolve(j.text); else reject(new Error((j.error && j.error.message) || 'Ошибка Whisper')); }
        catch { reject(new Error('Ошибка парсинга Whisper')); }
      });
    });
    req.on('error', reject); form.pipe(req);
  });
}

// ── Команды ───────────────────────────────────────────────────────────────────

bot.command('start', ctx => ctx.reply(
  'Claude Code Bridge\n\n' +
  'Отправь задачу текстом или голосом — выполню на VPS.\n\n' +
  '/ping   — проверить Claude Code\n' +
  '/reset  — новая сессия\n' +
  '/status — ID сессии\n' +
  '/cancel — остановить задачу\n' +
  '/logs   — логи бота\n' +
  '/files  — изменённые файлы\n' +
  '/where  — рабочая папка'
));

bot.command('ping', async ctx => {
  const start = Date.now();
  const msg = await ctx.reply('Проверяю...');
  try {
    const claudeBin = process.env.CLAUDE_BIN || 'claude';
    const version = execSync(claudeBin + ' --version 2>&1', { encoding: 'utf8' }).trim();
    const apiKey = process.env.ANTHROPIC_API_KEY ? 'есть' : 'ОТСУТСТВУЕТ!';
    await ctx.api.editMessageText(ctx.chat.id, msg.message_id,
      'Claude Code работает\n\n' +
      'Версия: ' + version + '\n' +
      'ANTHROPIC_API_KEY: ' + apiKey + '\n' +
      'Рабочая папка: ' + WORK_DIR + '\n' +
      'Время: ' + (Date.now() - start) + ' мс'
    );
  } catch (e) {
    await ctx.api.editMessageText(ctx.chat.id, msg.message_id, 'Claude Code не найден\n\n' + e.message);
  }
});

bot.command('reset', ctx => { sessions.delete(ctx.chat.id); return ctx.reply('Сессия сброшена.'); });

bot.command('status', ctx => {
  const s = sessions.get(ctx.chat.id);
  return ctx.reply(s ? 'Сессия: ' + s : 'Нет активной сессии.');
});

bot.command('cancel', ctx => {
  if (inFlight.get(ctx.chat.id) === 'running') {
    inFlight.set(ctx.chat.id, 'cancelled');
    return ctx.reply('Отмена запрошена.');
  }
  return ctx.reply('Нет активных задач.');
});

bot.command('where', ctx => ctx.reply('Рабочая папка: ' + WORK_DIR));

bot.command('logs', async ctx => {
  try {
    const out = execSync(
      'tail -30 /root/.pm2/logs/claude-telegram-bridge-out.log 2>/dev/null || echo "Лог пуст"',
      { encoding: 'utf8' }
    ).slice(-3500);
    await ctx.reply(out || 'Логи пусты.');
  } catch (e) { await ctx.reply('Ошибка: ' + e.message); }
});

bot.command('files', async ctx => {
  try {
    const out = execSync(
      'find ' + WORK_DIR + ' -newer ' + WORK_DIR + '/package.json -type f -not -path "*/node_modules/*" -not -path "*/.git/*" 2>/dev/null | head -20',
      { encoding: 'utf8' }
    );
    await ctx.reply(out.trim() || 'Изменённых файлов нет.');
  } catch (e) { await ctx.reply('Ошибка: ' + e.message); }
});

// ── Голосовые сообщения ───────────────────────────────────────────────────────

bot.on('message:voice', async ctx => {
  if (!isAllowed(ctx.from && ctx.from.id)) return ctx.reply('Доступ запрещён.');
  const statusMsg = await ctx.reply('Распознаю голос...');
  const chatId = ctx.chat.id;
  const msgId = statusMsg.message_id;
  try {
    const fileInfo = await ctx.api.getFile(ctx.message.voice.file_id);
    const url = 'https://api.telegram.org/file/bot' + TOKEN + '/' + fileInfo.file_path;
    const tmp = '/tmp/voice_' + Date.now() + '.ogg';
    await downloadFile(url, tmp);
    const text = await transcribeVoice(tmp);
    try { fs.unlinkSync(tmp); } catch {}
    await safeEdit(ctx, chatId, msgId, 'Вы сказали: ' + text + '\n\nВыполняю...');
    await processTask(ctx, chatId, msgId, text);
  } catch (err) {
    await safeEdit(ctx, chatId, msgId, 'Голос: ' + err.message);
  }
});

// ── Текстовые сообщения ───────────────────────────────────────────────────────

bot.on('message:text', async ctx => {
  if (!isAllowed(ctx.from && ctx.from.id)) return ctx.reply('Доступ запрещён.');
  const chatId = ctx.chat.id;
  if (inFlight.get(chatId) === 'running') return ctx.reply('Задача уже выполняется. /cancel для остановки.');
  const statusMsg = await ctx.reply('Выполняю...');
  await processTask(ctx, chatId, statusMsg.message_id, ctx.message.text.trim());
});

// ── Обработчик задач ──────────────────────────────────────────────────────────

async function processTask(ctx, chatId, msgId, prompt) {
  inFlight.set(chatId, 'running');
  let accumulated = '', lastEdit = 0, toolStatus = '';

  const flush = async (final) => {
    if (!accumulated && !final) return;
    if (!final && Date.now() - lastEdit < UPDATE_INTERVAL) return;
    lastEdit = Date.now();
    const body = accumulated.slice(-3600);
    const suffix = final ? '' : (toolStatus ? '\n\n' + toolStatus + '\n...' : '\n\nДумаю...');
    await safeEdit(ctx, chatId, msgId, body + suffix);
  };

  try {
    const { text: result, sessionId: newSid, toolsUsed } = await runClaude(prompt, {
      sessionId: sessions.get(chatId),
      onChunk: async chunk => {
        if (inFlight.get(chatId) === 'cancelled') return;
        accumulated += chunk; toolStatus = '';
        await flush(false);
      },
      onTool: async tool => {
        if (inFlight.get(chatId) === 'cancelled') return;
        toolStatus = tool.label + (tool.detail ? ': ' + tool.detail : '');
        await flush(false);
      },
    });

    if (newSid) sessions.set(chatId, newSid);
    if (!accumulated) accumulated = result;

    if (toolsUsed && toolsUsed.length > 0) {
      accumulated += '\n\n─────\nИспользовано: ' +
        [...new Set(toolsUsed.map(t => t.label))].join(', ');
    }

    if (accumulated.length > 4000) {
      const parts = splitText(accumulated, 4000);
      await safeEdit(ctx, chatId, msgId, parts[0]);
      for (let i = 1; i < parts.length; i++) await ctx.reply(parts[i]);
    } else {
      await safeEdit(ctx, chatId, msgId, accumulated);
    }
  } catch (err) {
    await safeEdit(ctx, chatId, msgId, 'Ошибка: ' + ((err && err.message) || String(err)));
  } finally {
    inFlight.delete(chatId);
  }
}

bot.catch(err => console.error('Ошибка бота:', err.message));
bot.start();

console.log('Claude Code Telegram bridge started.');
console.log('Work dir:', WORK_DIR);
console.log('Allowed IDs:', ALLOWED_IDS.length ? ALLOWED_IDS.join(', ') : 'ALL');
console.log('Voice:', OPENAI_API_KEY ? 'enabled' : 'disabled');
"""
write(os.path.join(BASE, 'bot.js'), bot_js)

# ── Шаг 6: Установка зависимостей ─────────────────────────────────────────────

header('6. Установка npm зависимостей')
run(f'cd {BASE} && npm install')

# ── Шаг 7: PM2 ────────────────────────────────────────────────────────────────

header('7. Настройка PM2')

# Установить PM2 если нет
pm2 = run('which pm2', capture=True, check=False)
if pm2.returncode != 0:
    print('  Устанавливаю PM2...')
    run('npm install -g pm2')

# Остановить старый процесс если есть
run('pm2 delete claude-telegram-bridge 2>/dev/null || true', check=False)

# Запустить
run(f'cd {BASE} && pm2 start bot.js --name claude-telegram-bridge')
run('pm2 save')

# Автозапуск
r = run('pm2 startup 2>&1 | tail -3', capture=True, check=False)
print(f'  PM2 startup: {r.stdout.strip()}')

# ── Шаг 8: Проверка ───────────────────────────────────────────────────────────

header('8. Проверка')
import time
time.sleep(2)
status = run('pm2 list 2>&1', capture=True)
print(status.stdout)

header('Готово!')
print('  Бот запущен через PM2.')
print('  Напиши /ping боту в Telegram — он должен ответить.')
print()
print('  Если Claude не отвечает на задачи — проверь ANTHROPIC_API_KEY:')
print(f'  cat {BASE}/.env | grep ANTHROPIC')
print()
print('  Логи: pm2 logs claude-telegram-bridge')

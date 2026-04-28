require('dotenv').config();
const { Bot, InputFile } = require('grammy');
const { runClaude } = require('./claude-runner');
const { execSync, exec } = require('child_process');
const fs = require('fs');
const path = require('path');
const https = require('https');

const TOKEN = process.env.TELEGRAM_BOT_TOKEN;
const ALLOWED_IDS = (process.env.ALLOWED_USER_IDS || '')
  .split(',').map(s => s.trim()).filter(Boolean).map(Number);
const UPDATE_INTERVAL = parseInt(process.env.STREAM_UPDATE_INTERVAL_MS || '2000', 10);
const WORK_DIR = process.env.WORK_DIR || process.cwd();
const OPENAI_API_KEY = process.env.OPENAI_API_KEY || '';

if (!TOKEN) { console.error('TELEGRAM_BOT_TOKEN not set'); process.exit(1); }

const bot = new Bot(TOKEN);
const sessions = new Map();
const inFlight = new Map();

function isAllowed(id) {
  return ALLOWED_IDS.length === 0 || ALLOWED_IDS.includes(id);
}

function splitText(text, maxLen) {
  const parts = [];
  let i = 0;
  while (i < text.length) { parts.push(text.slice(i, i + maxLen)); i += maxLen; }
  return parts;
}

function safeEdit(ctx, chatId, msgId, text) {
  return ctx.api.editMessageText(chatId, msgId, text || '…').catch(() => {});
}

// Download file from Telegram
function downloadFile(url, dest) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(dest);
    https.get(url, (res) => {
      res.pipe(file);
      file.on('finish', () => { file.close(); resolve(); });
    }).on('error', reject);
  });
}

// Transcribe voice via OpenAI Whisper
async function transcribeVoice(filePath) {
  if (!OPENAI_API_KEY) throw new Error('OPENAI_API_KEY не настроен в .env');
  const FormData = require('form-data');
  const form = new FormData();
  form.append('file', fs.createReadStream(filePath), { filename: 'voice.ogg', contentType: 'audio/ogg' });
  form.append('model', 'whisper-1');
  form.append('language', 'ru');

  return new Promise((resolve, reject) => {
    const req = https.request({
      hostname: 'api.openai.com',
      path: '/v1/audio/transcriptions',
      method: 'POST',
      headers: { ...form.getHeaders(), Authorization: 'Bearer ' + OPENAI_API_KEY },
    }, (res) => {
      let data = '';
      res.on('data', chunk => { data += chunk; });
      res.on('end', () => {
        try {
          const json = JSON.parse(data);
          if (json.text) resolve(json.text);
          else reject(new Error(json.error && json.error.message || 'Whisper error'));
        } catch { reject(new Error('Whisper parse error')); }
      });
    });
    req.on('error', reject);
    form.pipe(req);
  });
}

// ─── Commands ────────────────────────────────────────────────────────────────

bot.command('start', ctx => ctx.reply(
  'Claude Code Bridge\n\n' +
  'Отправь любую задачу текстом или голосом — выполню на VPS.\n\n' +
  '/ping    — проверить что Claude Code работает\n' +
  '/reset   — новая сессия (сброс контекста)\n' +
  '/status  — ID текущей сессии\n' +
  '/cancel  — отменить выполняющуюся задачу\n' +
  '/logs    — последние логи бота\n' +
  '/files   — недавно изменённые файлы\n' +
  '/where   — текущая рабочая папка'
));

bot.command('reset', ctx => {
  sessions.delete(ctx.chat.id);
  return ctx.reply('Сессия сброшена. Следующее сообщение начнёт новый разговор.');
});

bot.command('status', ctx => {
  const sid = sessions.get(ctx.chat.id);
  return ctx.reply(sid ? 'Сессия: ' + sid : 'Нет активной сессии.');
});

bot.command('cancel', ctx => {
  if (inFlight.get(ctx.chat.id) === 'running') {
    inFlight.set(ctx.chat.id, 'cancelled');
    return ctx.reply('Отмена запрошена — Claude остановится после текущего шага.');
  }
  return ctx.reply('Нет активных задач.');
});

bot.command('where', ctx => ctx.reply('Рабочая папка: ' + WORK_DIR));

bot.command('ping', async ctx => {
  const start = Date.now();
  const msg = await ctx.reply('Проверяю Claude Code...');
  try {
    const { execSync } = require('child_process');
    const claudeBin = process.env.CLAUDE_BIN || 'claude';
    const version = execSync(claudeBin + ' --version 2>&1', { encoding: 'utf8' }).trim();
    const elapsed = Date.now() - start;
    await ctx.api.editMessageText(ctx.chat.id, msg.message_id,
      'Claude Code работает\n\n' +
      'Версия: ' + version + '\n' +
      'Путь: ' + claudeBin + '\n' +
      'Рабочая папка: ' + WORK_DIR + '\n' +
      'Время ответа: ' + elapsed + ' мс'
    );
  } catch (e) {
    await ctx.api.editMessageText(ctx.chat.id, msg.message_id,
      'Claude Code не найден\n\nОшибка: ' + e.message + '\n\nПроверь CLAUDE_BIN в .env'
    );
  }
});

bot.command('logs', async (ctx) => {
  try {
    const out = execSync('pm2 logs claude-telegram-bridge --lines 30 --nostream 2>&1 || tail -30 ~/.pm2/logs/claude-telegram-bridge-out.log 2>/dev/null || echo "Логи недоступны"', { encoding: 'utf8' }).slice(-3500);
    await ctx.reply(out || 'Логи пусты.');
  } catch (e) {
    await ctx.reply('Ошибка чтения логов: ' + e.message);
  }
});

bot.command('files', async (ctx) => {
  try {
    const out = execSync('find ' + WORK_DIR + ' -newer ' + WORK_DIR + '/package.json -type f -not -path "*/node_modules/*" -not -path "*/.git/*" 2>/dev/null | head -20', { encoding: 'utf8' });
    await ctx.reply(out.trim() || 'Изменённых файлов не найдено.');
  } catch (e) {
    await ctx.reply('Ошибка: ' + e.message);
  }
});

// ─── Voice handler ───────────────────────────────────────────────────────────

bot.on('message:voice', async (ctx) => {
  if (!isAllowed(ctx.from && ctx.from.id)) return ctx.reply('Access denied.');

  const statusMsg = await ctx.reply('🎙 Распознаю голос…');
  const msgId = statusMsg.message_id;
  const chatId = ctx.chat.id;

  try {
    const fileId = ctx.message.voice.file_id;
    const fileInfo = await ctx.api.getFile(fileId);
    const fileUrl = 'https://api.telegram.org/file/bot' + TOKEN + '/' + fileInfo.file_path;
    const tmpPath = '/tmp/voice_' + Date.now() + '.ogg';

    await downloadFile(fileUrl, tmpPath);
    const text = await transcribeVoice(tmpPath);
    fs.unlinkSync(tmpPath);

    await safeEdit(ctx, chatId, msgId, '🎙 Вы сказали: ' + text + '\n\n⏳ Выполняю…');
    await processTask(ctx, chatId, msgId, text);
  } catch (err) {
    await safeEdit(ctx, chatId, msgId, '❌ Голос: ' + err.message + '\n\nДобавьте OPENAI_API_KEY в .env для распознавания речи.');
  }
});

// ─── Text handler ────────────────────────────────────────────────────────────

bot.on('message:text', async (ctx) => {
  if (!isAllowed(ctx.from && ctx.from.id)) return ctx.reply('Access denied.');

  const chatId = ctx.chat.id;
  if (inFlight.get(chatId) === 'running') {
    return ctx.reply('Задача уже выполняется. /cancel для остановки.');
  }

  const statusMsg = await ctx.reply('⏳ Выполняю…');
  await processTask(ctx, chatId, statusMsg.message_id, ctx.message.text.trim());
});

// ─── Core task processor ─────────────────────────────────────────────────────

async function processTask(ctx, chatId, msgId, prompt) {
  inFlight.set(chatId, 'running');

  let accumulated = '';
  let lastEdit = 0;
  let toolStatus = '';

  const flush = async (final) => {
    if (!accumulated && !final) return;
    const now = Date.now();
    if (!final && now - lastEdit < UPDATE_INTERVAL) return;
    lastEdit = now;

    const body = accumulated.slice(-3600);
    const indicator = final ? '' : (toolStatus ? '\n\n' + toolStatus + '\n…' : '\n\n⏳ Думаю…');
    await safeEdit(ctx, chatId, msgId, body + indicator);
  };

  try {
    const sessionId = sessions.get(chatId);

    const { text: result, sessionId: newSid, toolsUsed } = await runClaude(prompt, {
      sessionId,
      onChunk: async (chunk) => {
        if (inFlight.get(chatId) === 'cancelled') return;
        accumulated += chunk;
        toolStatus = '';
        await flush(false);
      },
      onTool: async (tool) => {
        if (inFlight.get(chatId) === 'cancelled') return;
        toolStatus = tool.label + (tool.detail ? ': `' + tool.detail + '`' : '');
        await flush(false);
      },
    });

    if (newSid) sessions.set(chatId, newSid);
    if (!accumulated) accumulated = result;

    // Append tools summary
    if (toolsUsed && toolsUsed.length > 0) {
      const summary = '\n\n─────\n🛠 Использовано: ' +
        toolsUsed.map(t => t.label + (t.detail ? ' `' + t.detail.slice(0, 30) + '`' : '')).join(', ');
      accumulated += summary;
    }

    if (accumulated.length > 4000) {
      const parts = splitText(accumulated, 4000);
      await safeEdit(ctx, chatId, msgId, parts[0]);
      for (let i = 1; i < parts.length; i++) await ctx.reply(parts[i]);
    } else {
      await safeEdit(ctx, chatId, msgId, accumulated);
    }

  } catch (err) {
    const msg = '❌ ' + (err && err.message ? err.message : String(err));
    await safeEdit(ctx, chatId, msgId, msg);
  } finally {
    inFlight.delete(chatId);
  }
}

bot.catch(err => console.error('Bot error:', err.message));
bot.start();

console.log('Claude Code Telegram bridge started.');
console.log('Work dir:', WORK_DIR);
console.log('Allowed IDs:', ALLOWED_IDS.length ? ALLOWED_IDS.join(', ') : 'ALL');
console.log('Voice (Whisper):', OPENAI_API_KEY ? 'enabled' : 'disabled (add OPENAI_API_KEY to .env)');

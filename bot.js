require('dotenv').config();
const { Bot } = require('grammy');
const { runClaude } = require('./claude-runner');

const TOKEN = process.env.TELEGRAM_BOT_TOKEN;
const ALLOWED_IDS = (process.env.ALLOWED_USER_IDS || '')
  .split(',')
  .map(s => s.trim())
  .filter(Boolean)
  .map(Number);
const UPDATE_INTERVAL = parseInt(process.env.STREAM_UPDATE_INTERVAL_MS || '2000', 10);

if (!TOKEN) {
  console.error('TELEGRAM_BOT_TOKEN is not set in .env');
  process.exit(1);
}

const bot = new Bot(TOKEN);

// chatId -> sessionId for conversation continuity
const sessions = new Map();
// chatId -> 'running' | 'cancelled'
const inFlight = new Map();

function isAllowed(userId) {
  if (ALLOWED_IDS.length === 0) return true;
  return ALLOWED_IDS.includes(userId);
}

function splitText(text, maxLen) {
  const parts = [];
  let i = 0;
  while (i < text.length) {
    parts.push(text.slice(i, i + maxLen));
    i += maxLen;
  }
  return parts;
}

bot.command('start', async (ctx) => {
  await ctx.reply(
    'Claude Code Bridge\n\n' +
    'Send me any task — I\'ll run it with Claude Code on the VPS.\n\n' +
    '/reset — start a new conversation session\n' +
    '/status — show current session ID\n' +
    '/cancel — cancel running task'
  );
});

bot.command('help', async (ctx) => ctx.reply(
  'Just send a message with your task.\n\n' +
  '/reset — new session\n' +
  '/status — session info\n' +
  '/cancel — stop current task'
));

bot.command('reset', async (ctx) => {
  sessions.delete(ctx.chat.id);
  await ctx.reply('Session reset. Next message starts a fresh conversation.');
});

bot.command('status', async (ctx) => {
  const sid = sessions.get(ctx.chat.id);
  await ctx.reply(sid ? `Session ID: ${sid}` : 'No active session.');
});

bot.command('cancel', async (ctx) => {
  if (inFlight.get(ctx.chat.id) === 'running') {
    inFlight.set(ctx.chat.id, 'cancelled');
    await ctx.reply('Cancellation requested.');
  } else {
    await ctx.reply('No task is currently running.');
  }
});

bot.on('message:text', async (ctx) => {
  const chatId = ctx.chat.id;
  const userId = ctx.from?.id;
  const text = ctx.message.text.trim();

  if (!isAllowed(userId)) {
    await ctx.reply('Access denied.');
    return;
  }

  if (inFlight.get(chatId) === 'running') {
    await ctx.reply('A task is already running. Send /cancel to stop it.');
    return;
  }

  inFlight.set(chatId, 'running');

  const statusMsg = await ctx.reply('⏳ Running…');
  const msgId = statusMsg.message_id;

  let accumulated = '';
  let lastEditedAt = 0;

  const flushEdit = async (final = false) => {
    if (!accumulated) return;
    const now = Date.now();
    if (!final && now - lastEditedAt < UPDATE_INTERVAL) return;
    lastEditedAt = now;

    const preview = accumulated.slice(-3800);
    const display = (final ? '' : '⏳ ') + preview + (final ? '' : '\n…');
    try {
      await ctx.api.editMessageText(chatId, msgId, display);
    } catch {
      // unchanged content or rate limit — skip
    }
  };

  try {
    const sessionId = sessions.get(chatId);

    const { text: result, sessionId: newSessionId } = await runClaude(text, {
      sessionId,
      onChunk: async (chunk) => {
        if (inFlight.get(chatId) === 'cancelled') return;
        accumulated += chunk;
        await flushEdit(false);
      },
    });

    if (newSessionId) sessions.set(chatId, newSessionId);
    if (!accumulated) accumulated = result;

    if (accumulated.length > 4000) {
      const parts = splitText(accumulated, 4000);
      await ctx.api.editMessageText(chatId, msgId, parts[0]);
      for (let i = 1; i < parts.length; i++) {
        await ctx.reply(parts[i]);
      }
    } else {
      await flushEdit(true);
    }

  } catch (err) {
    const errMsg = err?.message || String(err);
    try {
      await ctx.api.editMessageText(chatId, msgId, `❌ Error: ${errMsg}`);
    } catch {
      await ctx.reply(`❌ Error: ${errMsg}`);
    }
  } finally {
    inFlight.delete(chatId);
  }
});

bot.catch((err) => {
  console.error('Bot error:', err.message);
});

bot.start();
console.log('Claude Code Telegram bridge started.');
console.log(`Allowed user IDs: ${ALLOWED_IDS.length ? ALLOWED_IDS.join(', ') : 'ALL (no restriction)'}`);

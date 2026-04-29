#!/bin/bash
# OAuth авторизация Claude Code (без API ключа)

set -e

CLAUDE=$(which claude 2>/dev/null || echo "")

echo ""
echo "════════════════════════════════════════════"
echo "   Авторизация Claude Code через браузер"
echo "════════════════════════════════════════════"
echo ""

# Проверить claude
if [ -z "$CLAUDE" ]; then
  echo "❌ claude не найден в PATH"
  echo "   Установи: npm install -g @anthropic-ai/claude-code"
  exit 1
fi

echo "✅ Claude найден: $CLAUDE"
echo "   Версия: $($CLAUDE --version 2>&1 | head -1)"
echo ""

# Проверить уже авторизован?
if [ -f "$HOME/.claude/.credentials.json" ] || [ -f "$HOME/.claude/credentials.json" ]; then
  echo "🔍 Найдена сохранённая сессия. Проверяю..."
  RESULT=$(timeout 30 "$CLAUDE" --print --dangerously-skip-permissions --output-format json "say: OK" 2>&1 || true)
  if echo "$RESULT" | grep -qi "ok"; then
    echo "✅ Уже авторизован! Повторный вход не нужен."
    echo ""
    echo "Перезапусти бот если нужно: pm2 restart claude-telegram-bridge"
    exit 0
  fi
  echo "⚠️  Сессия устарела, нужно войти заново."
  echo ""
fi

echo "Сейчас откроется интерактивный Claude."
echo ""
echo "Что делать:"
echo "  1. Claude покажет URL — скопируй его"
echo "  2. Открой URL в браузере на своём компьютере"
echo "  3. Войди через claude.ai аккаунт"
echo "  4. После успешного входа вернись сюда и нажми Ctrl+C"
echo ""
echo "Нажми Enter чтобы начать..."
read -r

# Убираем пустой ключ чтобы не мешал OAuth
unset ANTHROPIC_API_KEY

echo ""
echo "── Запускаю claude (Ctrl+C когда войдёшь) ──"
echo ""

# Запускаем интерактивно — Claude сам покажет ссылку для входа
"$CLAUDE" || true

echo ""
echo "── Проверяю авторизацию ──"
echo ""

RESULT=$(timeout 30 "$CLAUDE" --print --dangerously-skip-permissions --output-format json "say: WORKS" 2>&1 || true)

if echo "$RESULT" | grep -qi "works"; then
  echo "✅ Авторизация успешна!"
  echo ""
  echo "Перезапускаю бот..."
  pm2 restart claude-telegram-bridge 2>/dev/null && echo "✅ Бот перезапущен." || echo "⚠️  pm2 не найден, запусти вручную: pm2 restart claude-telegram-bridge"
else
  echo "❌ Проверка не прошла. Попробуй ещё раз."
  echo ""
  echo "Вывод Claude:"
  echo "$RESULT" | head -10
  exit 1
fi

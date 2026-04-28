#!/bin/bash
# Авторизация Claude Code на сервере

CLAUDE=$(which claude 2>/dev/null || echo "/usr/bin/claude")

echo "════════════════════════════════════════"
echo "  Авторизация Claude Code"
echo "════════════════════════════════════════"
echo ""
echo "Claude откроет ссылку — скопируй её,"
echo "открой в браузере на своём компьютере,"
echo "войди в аккаунт claude.ai"
echo ""
echo "Нажми Enter чтобы начать..."
read

# Запускаем claude — он сам покажет URL для входа
$CLAUDE --print "test" 2>&1 | head -5 &
CPID=$!
sleep 2
kill $CPID 2>/dev/null

echo ""
echo "Если URL не появился — запусти просто:"
echo "  $CLAUDE"
echo ""
echo "После входа нажми Ctrl+C и выполни:"
echo "  pm2 restart claude-telegram-bridge"

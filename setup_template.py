
def run(cmd, check=True, capture=False, timeout=30):
    kw = dict(shell=True, text=True, timeout=timeout)
    if capture:
        kw['stdout'] = subprocess.PIPE
        kw['stderr'] = subprocess.PIPE
    try:
        result = subprocess.run(cmd, **kw)
        if check and not capture and result.returncode != 0:
            print(f"  ОШИБКА [{result.returncode}]: {cmd[:80]}")
        return result
    except subprocess.TimeoutExpired:
        print(f"  ТАЙМАУТ: {cmd[:80]}")
        class T:
            returncode = 1
            stdout = ""
            stderr = "timeout"
        return T()

def write_binary(path, b64data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(base64.b64decode(b64data))

def write_text(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)

def header(msg):
    print(f"\n{'─'*52}\n  {msg}\n{'─'*52}")

# ── 1. Найти Claude ──────────────────────────────────────────────────────────
header("1. Поиск Claude Binary")
claude_bin = ""
for p in ["/usr/bin/claude", "/opt/node22/bin/claude", "/usr/local/bin/claude"]:
    if os.path.exists(p):
        claude_bin = p
        break
if not claude_bin:
    r = run("which claude 2>/dev/null", capture=True, check=False)
    if r.returncode == 0:
        claude_bin = r.stdout.strip()

if not claude_bin:
    print("  ОШИБКА: Claude не найден!")
    sys.exit(1)

ver = run(f"{claude_bin} --version 2>&1", capture=True)
print(f"  Найден:  {claude_bin}")
print(f"  Версия:  {ver.stdout.strip()}")

# ── 2. Тест Claude ───────────────────────────────────────────────────────────
header("2. Тест Claude (критически важно)")
print("  Запускаю тест... (до 40 сек)")

env_for_test = os.environ.copy()
# Убираем пустой ключ чтобы не мешал OAuth
if not env_for_test.get('ANTHROPIC_API_KEY'):
    env_for_test.pop('ANTHROPIC_API_KEY', None)

try:
    test = subprocess.run(
        [claude_bin, '--print', '--dangerously-skip-permissions',
         '--output-format', 'json', 'say exactly: WORKS'],
        capture_output=True, text=True, timeout=45, env=env_for_test
    )
    claude_ok = test.returncode == 0 and 'WORKS' in (test.stdout + test.stderr).upper()
    print(f"  Код: {test.returncode}")
    out = (test.stdout + test.stderr)[:400]
    print(f"  Вывод: {out}")
except subprocess.TimeoutExpired:
    claude_ok = False
    print("  ТАЙМАУТ — Claude завис. OAuth сессия, возможно, истекла.")
    test = type('T', (), {'stdout': '', 'stderr': 'timeout', 'returncode': 1})()

# Определить причину сбоя
api_key = ""
if not claude_ok:
    output_combined = getattr(test, 'stdout', '') + getattr(test, 'stderr', '')
    needs_key = any(x in output_combined.lower() for x in [
        'api key', 'apikey', 'anthropic_api_key', 'authentication', 'auth', 'unauthorized', '401'
    ])
    print()
    if needs_key or 'timeout' in output_combined.lower():
        print("  ⚠️  Claude требует ANTHROPIC_API_KEY")
        print("  Получи ключ: https://console.anthropic.com/settings/keys")
        try:
            api_key = input("  Вставь ключ (sk-ant-...): ").strip()
        except EOFError:
            api_key = ""

        if api_key:
            env2 = env_for_test.copy()
            env2['ANTHROPIC_API_KEY'] = api_key
            print("  Проверяю с ключом...")
            try:
                test2 = subprocess.run(
                    [claude_bin, '--print', '--dangerously-skip-permissions',
                     '--output-format', 'json', 'say exactly: WORKS'],
                    capture_output=True, text=True, timeout=45, env=env2
                )
                if test2.returncode == 0:
                    print("  ✅ Работает с API ключом!")
                    claude_ok = True
                else:
                    print(f"  ❌ {(test2.stdout+test2.stderr)[:200]}")
            except subprocess.TimeoutExpired:
                print("  ❌ Снова таймаут")
    else:
        print("  ⚠️  Claude не ответил. Бот будет запущен, но задачи могут не выполняться.")
        print("  После установки запусти вручную: claude  — и войди в аккаунт.")
else:
    print("  ✅ Claude работает!")

# ── 3. Файлы ─────────────────────────────────────────────────────────────────
header("3. Создание файлов проекта")
os.makedirs(BASE, exist_ok=True)

pkg = {
    "name": "vps-claude-telegram-bridge",
    "version": "1.0.0",
    "main": "bot.js",
    "type": "commonjs",
    "dependencies": {
        "dotenv": "^16.4.5",
        "grammy": "^1.42.0",
        "form-data": "^4.0.0"
    }
}
write_text(os.path.join(BASE, "package.json"), json.dumps(pkg, indent=2))
print("  OK: package.json")

write_binary(os.path.join(BASE, "bot.js"), BOT_B64)
print("  OK: bot.js (с кнопками клавиатуры)")

write_binary(os.path.join(BASE, "claude-runner.js"), RUNNER_B64)
print("  OK: claude-runner.js")

# ── 4. .env ──────────────────────────────────────────────────────────────────
header("4. Конфигурация .env")
env_path = os.path.join(BASE, ".env")
existing = {}
if os.path.exists(env_path):
    for line in open(env_path):
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, _, v = line.partition('=')
            existing[k.strip()] = v.strip()

defaults = {
    "TELEGRAM_BOT_TOKEN": "8766937307:AAGm1YC9VWsVLH-_hlDDdj8WSLqyynXvGFA",
    "ALLOWED_USER_IDS": "1264067528",
    "WORK_DIR": BASE,
    "CLAUDE_BIN": claude_bin,
    "CLAUDE_TIMEOUT_MS": "300000",
    "STREAM_UPDATE_INTERVAL_MS": "2000",
    "OPENAI_API_KEY": "",
}
if api_key:
    defaults["ANTHROPIC_API_KEY"] = api_key

for k, v in defaults.items():
    if k not in existing:
        existing[k] = v

# Убрать пустой ANTHROPIC_API_KEY чтобы не ломал OAuth
if not existing.get("ANTHROPIC_API_KEY"):
    existing.pop("ANTHROPIC_API_KEY", None)

with open(env_path, 'w') as f:
    for k, v in existing.items():
        f.write(f"{k}={v}\n")

has_key = bool(existing.get("ANTHROPIC_API_KEY"))
print(f"  OK: .env — авторизация: {'API ключ' if has_key else 'OAuth ~/.claude/'}")

# ── 5. npm install ───────────────────────────────────────────────────────────
header("5. Установка зависимостей")
r = run(f"cd {BASE} && npm install 2>&1", capture=True)
lines_out = [l for l in r.stdout.splitlines() if l.strip() and 'npm warn' not in l.lower()]
print('\n'.join(f"  {l}" for l in lines_out[-5:]))

# ── 6. PM2 ───────────────────────────────────────────────────────────────────
header("6. Запуск через PM2")
pm2_check = run("which pm2 2>/dev/null", capture=True, check=False)
if pm2_check.returncode != 0:
    print("  Устанавливаю PM2...")
    run("npm install -g pm2 2>&1")

run("pm2 delete claude-telegram-bridge 2>/dev/null; true", check=False)
time.sleep(1)
run(f"cd {BASE} && pm2 start bot.js --name claude-telegram-bridge 2>&1")
run("pm2 save 2>&1")

time.sleep(3)
status = run("pm2 list 2>&1", capture=True)
print(status.stdout)

# ── Итог ─────────────────────────────────────────────────────────────────────
header("ИТОГ")
if claude_ok:
    print("  ✅ Всё готово!")
    print()
    print("  В Telegram напиши боту /start")
    print("  Появятся кнопки: 📊 Логи  📁 Файлы  🔍 Пинг  и др.")
    print("  Тест: напиши 'сколько сейчас времени на сервере'")
else:
    print("  ⚠️  Бот запущен, но Claude не прошёл тест авторизации.")
    print()
    print("  Варианты исправления:")
    print("  1) Войди в Claude интерактивно: claude (и авторизуйся)")
    print("     Затем: pm2 restart claude-telegram-bridge")
    print()
    print("  2) Или добавь API ключ:")
    print(f"     echo 'ANTHROPIC_API_KEY=sk-ant-...' >> {BASE}/.env")
    print(f"     pm2 restart claude-telegram-bridge")
    print()
    print("  Логи бота: pm2 logs claude-telegram-bridge --lines 20")

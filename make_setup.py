#!/usr/bin/env python3
import base64, os

bot_b64 = base64.b64encode(open('/home/user/VPS-ClaudeCode/bot.js', 'rb').read()).decode()
runner_b64 = base64.b64encode(open('/home/user/VPS-ClaudeCode/claude-runner.js', 'rb').read()).decode()

lines = []
lines.append('#!/usr/bin/env python3')
lines.append('import os, sys, subprocess, base64, json, time')
lines.append('')
lines.append('BASE = "/home/user/VPS-ClaudeCode"')
lines.append('BOT_B64 = "' + bot_b64 + '"')
lines.append('RUNNER_B64 = "' + runner_b64 + '"')
lines.append('')
lines.append(open('/home/user/VPS-ClaudeCode/setup_template.py').read())

content = '\n'.join(lines)
with open('/home/user/VPS-ClaudeCode/setup.py', 'w') as f:
    f.write(content)
print('Done:', len(content), 'bytes')

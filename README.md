# AI Quotas Widget (Übersicht)

A sleek macOS desktop widget for [Übersicht](https://tracesof.net/uebersicht/) that aggregates real-time remaining quotas and account balances across multiple AI coding providers, and writes a local JSON snapshot (`~/.cache/ai-quotas.json`) for multi-provider agent routers (such as T3 Code).

## Supported Providers

- **Codex** — reads the latest `account/rateLimits/updated` event from T3 Code's local provider log (`~/.t3/userdata/logs/provider/events._global.log`).
- **Google Antigravity (Multi-Account)** — queries `antigravity -p "/usage"` per isolated `HOME` profile directory (supports multiple Google accounts without macOS Keychain collisions).
- **GitHub Copilot** — queries `gh api /copilot_internal/user` for Premium Interactions quota and reset date.
- **OpenCode Go** — queries `https://opencode.ai/inference/go/v1/usage` for 5-Hour, Weekly, and Monthly remaining quotas.
- **DeepSeek** — queries `https://api.deepseek.com/user/balance` for CNY/USD account balance.

## Features

- Dark frosted-glass macOS desktop card with color-coded progress bars and reset countdowns.
- Draggable header with persisted screen position (double-click header to reset to top-right).
- Auto-refreshes every 1 minute, plus a manual `↻` refresh button.
- Built-in HTTP/HTTPS proxy support.
- Atomically writes `~/.cache/ai-quotas.json` with T3 Code `providerInstanceId` mappings on every refresh.

## Quick Start

1. Install [Übersicht](https://tracesof.net/uebersicht/).
2. Run the installer:
   ```bash
   chmod +x install.sh && ./install.sh
   ```
3. Edit `~/Library/Application Support/Übersicht/widgets/ai-quotas.widget/config.json`:
   ```json
   {
     "proxy": "http://127.0.0.1:7899",
     "deepseekApiKey": "sk-...",
     "opencodeGoApiKey": "sk-...",
     "antigravityAccounts": [
       { "name": "Antigravity 1", "homeDir": "~/.ag-quota-profiles/acc1" },
       { "name": "Antigravity 2", "homeDir": "~/.ag-quota-profiles/acc2" }
     ]
   }
   ```
   *(Leave `proxy` empty if you don't need a proxy.)*

### Multi-Account Antigravity Setup (macOS)

To isolate multiple Antigravity personal Google accounts without overwriting macOS Keychain:

```bash
mkdir -p ~/.ag-quota-profiles/acc1 ~/.ag-quota-profiles/acc2

# Sign in Account 1
HOME="$HOME/.ag-quota-profiles/acc1" AGY_ACP_FORCE_FILE_STORAGE=1 SSH_CONNECTION="127.0.0.1 0 127.0.0.1 0" \
  /path/to/antigravity -p "/usage"

# Sign in Account 2
HOME="$HOME/.ag-quota-profiles/acc2" AGY_ACP_FORCE_FILE_STORAGE=1 SSH_CONNECTION="127.0.0.1 0 127.0.0.1 0" \
  /path/to/antigravity -p "/usage"
```

## Local JSON Snapshot

Every refresh writes `~/.cache/ai-quotas.json` so scripts or AI orchestrators can read live quotas in milliseconds without spawning subprocesses.

## License

MIT

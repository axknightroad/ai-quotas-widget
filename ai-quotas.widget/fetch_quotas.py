#!/usr/bin/env python3
import concurrent.futures
import glob
import json
import os
import re
import subprocess
import urllib.request
from datetime import datetime, timezone

WIDGET_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(WIDGET_DIR, "config.json")


def load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def find_antigravity_bin():
    pattern = os.path.expanduser(
        "~/.t3/tools/antigravity-acp/darwin-arm64/versions/*/antigravity"
    )
    matches = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
    return matches[0] if matches else None


def base_env(proxy):
    env = os.environ.copy()
    env["PATH"] = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:" + env.get("PATH", "")
    if proxy:
        env["HTTP_PROXY"] = proxy
        env["HTTPS_PROXY"] = proxy
        env["NO_PROXY"] = "localhost,127.0.0.1,::1,.local"
    return env


def format_reset_epoch(epoch_sec):
    if not epoch_sec:
        return ""
    now = datetime.now(timezone.utc).timestamp()
    diff = int(epoch_sec - now)
    if diff <= 0:
        return "now"
    days, rem = divmod(diff, 86400)
    hours, rem = divmod(rem, 3600)
    mins = rem // 60
    if days > 0:
        return f"{days}d {hours}h"
    if hours > 0:
        return f"{hours}h {mins}m"
    return f"{mins}m"


def format_reset_iso(iso_str):
    if not iso_str:
        return ""
    try:
        s = iso_str.strip()
        if s.endswith("Z"):
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
            return format_reset_epoch(dt.timestamp())
        return s
    except Exception:
        return iso_str


def fetch_codex():
    log_path = os.path.expanduser("~/.t3/userdata/logs/provider/events._global.log")
    if not os.path.exists(log_path):
        return {"name": "Codex", "status": "error", "error": "No T3 event log"}
    try:
        last_rl = None
        with open(log_path, "rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(max(0, size - 512 * 1024))
            chunk = f.read().decode("utf-8", errors="ignore")
        for line in chunk.splitlines():
            if "account/rateLimits/updated" not in line:
                continue
            idx = line.find("{")
            if idx == -1:
                continue
            try:
                obj = json.loads(line[idx:])
                rl = obj.get("event", {}).get("payload", {}).get("params", {}).get("rateLimits")
                if rl:
                    last_rl = rl
            except Exception:
                continue
        if not last_rl:
            return {"name": "Codex", "status": "empty", "error": "No rate limit data yet"}

        bars = []
        for key, default_label in [("primary", "Weekly"), ("secondary", "5-Hour")]:
            bucket = last_rl.get(key)
            if not bucket:
                continue
            used = bucket.get("usedPercent", 0)
            left = max(0, min(100, 100 - used))
            mins = bucket.get("windowDurationMins", 0)
            label = "Weekly" if mins >= 10000 else ("5-Hour" if mins == 300 else default_label)
            resets = format_reset_epoch(bucket.get("resetsAt"))
            bars.append({"label": label, "percent": left, "reset": resets})
        return {
            "name": "Codex",
            "plan": last_rl.get("planType") or "",
            "status": "ok",
            "bars": bars,
        }
    except Exception as e:
        return {"name": "Codex", "status": "error", "error": str(e)}


def fetch_antigravity_account(account, bin_path, proxy):
    name = account.get("name", "Antigravity")
    home_dir = account.get("homeDir", "")
    if not bin_path:
        return {"name": name, "status": "error", "error": "antigravity binary not found"}
    try:
        env = base_env(proxy)
        if home_dir:
            env["HOME"] = os.path.expanduser(home_dir)
            env["AGY_ACP_FORCE_FILE_STORAGE"] = "1"
            env["SSH_CONNECTION"] = "127.0.0.1 0 127.0.0.1 0"
        proc = subprocess.run(
            [bin_path, "-p", "/usage", "--print-timeout", "22s"],
            env=env,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=25,
        )
        out = proc.stdout.strip()
        if "Authentication required" in out or "Authentication required" in proc.stderr:
            return {"name": name, "status": "unconfigured", "error": "Not signed in yet"}
        if proc.returncode != 0 or not out:
            err = (proc.stderr or out or f"exit {proc.returncode}").strip().splitlines()[-1]
            return {"name": name, "status": "error", "error": err[:80]}

        bars = []
        for line in out.splitlines():
            line = line.strip()
            if not line or line.lower().startswith("quota:"):
                continue
            m = re.match(
                r"^(.+?)\s+(Weekly Limit Remaining|Five Hour Limit Remaining)\s+(\d+)%\s*(.*)$",
                line,
            )
            if not m:
                continue
            group, window, pct, reset_raw = m.groups()
            short_group = "Gemini" if "Gemini" in group else "Claude/GPT"
            short_win = "Weekly" if "Weekly" in window else "5h"
            bars.append(
                {
                    "label": f"{short_group} · {short_win}",
                    "percent": int(pct),
                    "reset": format_reset_iso(reset_raw),
                }
            )
        if not bars:
            return {"name": name, "status": "error", "error": "Could not parse /usage"}
        return {"name": name, "status": "ok", "bars": bars}
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or b"").decode("utf-8", errors="ignore") if isinstance(e.stdout, bytes) else (e.stdout or "")
        if "Authentication required" in out:
            return {"name": name, "status": "unconfigured", "error": "Not signed in yet"}
        return {"name": name, "status": "error", "error": "Timed out"}
    except Exception as e:
        return {"name": name, "status": "error", "error": str(e)[:80]}


def fetch_copilot(proxy):
    try:
        env = base_env(proxy)
        proc = subprocess.run(
            ["gh", "api", "/copilot_internal/user"],
            env=env,
            capture_output=True,
            text=True,
            timeout=15,
        )
        if proc.returncode != 0:
            err = (proc.stderr or "gh api failed").strip().splitlines()[-1]
            return {"name": "GitHub Copilot", "status": "error", "error": err[:80]}
        data = json.loads(proc.stdout)
        plan = data.get("copilot_plan", "")
        reset = format_reset_iso(data.get("quota_reset_date_utc", ""))
        prem = data.get("quota_snapshots", {}).get("premium_interactions", {})
        pct = prem.get("percent_remaining", 0)
        rem = prem.get("remaining", 0)
        ent = prem.get("entitlement", 0)
        bars = [
            {
                "label": f"Premium ({rem}/{ent})",
                "percent": round(pct, 1),
                "reset": reset,
            }
        ]
        return {"name": "GitHub Copilot", "plan": plan, "status": "ok", "bars": bars}
    except Exception as e:
        return {"name": "GitHub Copilot", "status": "error", "error": str(e)[:80]}


def fetch_opencode_go(api_key, proxy):
    key = (api_key or os.environ.get("OPENCODE_GO_API_KEY", "")).strip()
    if not key:
        return {
            "name": "OpenCode Go",
            "plan": "deepseek-official",
            "status": "unconfigured",
            "error": "Set opencodeGoApiKey in config.json",
        }
    try:
        handlers = []
        if proxy:
            handlers.append(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
        opener = urllib.request.build_opener(*handlers)
        req = urllib.request.Request(
            "https://opencode.ai/inference/go/v1/usage",
            headers={
                "Authorization": f"Bearer {key}",
                "Accept": "application/json",
                "User-Agent": "ai-quotas-widget/1.0",
            },
        )
        with opener.open(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        usage = data.get("usage", data)
        bars = []
        for key_name, label in [("rolling", "5-Hour"), ("weekly", "Weekly"), ("monthly", "Monthly")]:
            bucket = usage.get(key_name)
            if not isinstance(bucket, dict):
                continue
            used = bucket.get("percent", 0)
            left = max(0, min(100, 100 - used))
            reset = format_reset_iso(bucket.get("resetsAt", ""))
            bars.append({"label": label, "percent": left, "reset": reset})
        return {
            "name": "OpenCode Go",
            "plan": "deepseek-official",
            "status": "ok",
            "bars": bars,
        }
    except Exception as e:
        return {
            "name": "OpenCode Go",
            "plan": "deepseek-official",
            "status": "error",
            "error": str(e)[:80],
        }


def fetch_deepseek(api_key, proxy):
    key = (api_key or os.environ.get("DEEPSEEK_API_KEY", "")).strip()
    if not key:
        return {
            "name": "DeepSeek",
            "status": "unconfigured",
            "error": "Set deepseekApiKey in config.json",
        }
    try:
        handlers = []
        if proxy:
            handlers.append(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
        opener = urllib.request.build_opener(*handlers)
        req = urllib.request.Request(
            "https://api.deepseek.com/user/balance",
            headers={
                "Authorization": f"Bearer {key}",
                "Accept": "application/json",
            },
        )
        with opener.open(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        infos = data.get("balance_infos", [])
        balances = []
        for info in infos:
            curr = info.get("currency", "CNY")
            sym = "¥" if curr == "CNY" else "$"
            total = info.get("total_balance", "0")
            balances.append(f"{sym}{total} {curr}")
        return {
            "name": "DeepSeek",
            "status": "ok",
            "balanceText": " · ".join(balances) if balances else "¥0.00",
            "available": data.get("is_available", True),
        }
    except Exception as e:
        return {"name": "DeepSeek", "status": "error", "error": str(e)[:80]}


CACHE_PATH = os.path.expanduser("~/.cache/ai-quotas.json")

PROVIDER_ID_MAP = {
    "Codex": "codex",
    "Antigravity 1": "antigravity",
    "Antigravity 2": "antigravity_2",
    "GitHub Copilot": "acpRegistry_github_copilot",
    "OpenCode Go": "acpRegistry_deepseekharness",
    "DeepSeek": "acpRegistry_deepseekharness",
}


def write_cache(result):
    try:
        os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
        tmp_path = CACHE_PATH + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, CACHE_PATH)
    except Exception:
        pass


def main():
    cfg = load_config()
    proxy = cfg.get("proxy", "")
    ag_bin = find_antigravity_bin()
    ag_accounts = cfg.get("antigravityAccounts", [])

    with concurrent.futures.ThreadPoolExecutor(max_workers=7) as pool:
        f_codex = pool.submit(fetch_codex)
        f_copilot = pool.submit(fetch_copilot, proxy)
        f_opencode = pool.submit(fetch_opencode_go, cfg.get("opencodeGoApiKey", ""), proxy)
        f_deepseek = pool.submit(fetch_deepseek, cfg.get("deepseekApiKey", ""), proxy)
        f_ags = [
            pool.submit(fetch_antigravity_account, acc, ag_bin, proxy)
            for acc in ag_accounts
        ]

        providers = [f_codex.result()]
        for f_ag in f_ags:
            providers.append(f_ag.result())
        providers.append(f_copilot.result())
        providers.append(f_opencode.result())
        providers.append(f_deepseek.result())

    for p in providers:
        if p.get("name") in PROVIDER_ID_MAP:
            p["providerInstanceId"] = PROVIDER_ID_MAP[p["name"]]

    now_local = datetime.now().astimezone()
    result = {
        "updatedAt": now_local.strftime("%H:%M"),
        "updatedAtIso": now_local.isoformat(),
        "providers": providers,
    }
    write_cache(result)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()

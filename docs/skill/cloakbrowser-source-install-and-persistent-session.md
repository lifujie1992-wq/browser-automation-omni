# CloakBrowser Source Install and Persistent Session Notes

Session learning from installing/recovering CloakBrowser from the exact upstream `https://github.com/CloakHQ/CloakBrowser` on macOS.

## What CloakBrowser is in this setup

CloakBrowser from `CloakHQ/CloakBrowser` is not necessarily a normal `/Applications/CloakBrowser.app` GUI app. It is primarily a Python/Node library that launches a patched Chromium binary.

So absence of `CloakBrowser.app` does not mean it is fully missing. Check the binary cache and package install state.

## Source-first install workflow

```bash
mkdir -p ${TOOLS_DIR}
git clone https://github.com/CloakHQ/CloakBrowser ${CLOAKBROWSER_REPO}
cd ${CLOAKBROWSER_REPO}
python3 -m venv .venv
${CLOAKBROWSER_PY} -m pip install --upgrade pip
${CLOAKBROWSER_PY} -m pip install -e ${CLOAKBROWSER_REPO}
${CLOAKBROWSER_PY} -m cloakbrowser info
```

Upstream README says first launch auto-downloads the stealth Chromium binary into the user cache.

## Useful local checks

```bash
python3 -m pip show cloakbrowser 2>/dev/null || true
command -v cloakbrowser || true
find ${HOME} -maxdepth 4 \( -iname '*cloakbrowser*' -o -iname '*cloak*' \) 2>/dev/null | head -100
find ${CLOAKBROWSER_HOME} -maxdepth 3 -type f | head
ps aux | grep -E '${CLOAKBROWSER_HOME}/.*/Chromium|launch_doudian|CloakBrowser' | grep -v grep || true
```

In this session, useful paths were:

```text
${CLOAKBROWSER_REPO}
${CLOAKBROWSER_REPO}/.venv
${CLOAKBROWSER_HOME}
${CLOAKBROWSER_HOME}/chromium-145.0.7632.109.2/Chromium.app/Contents/MacOS/Chromium
${CLOAKBROWSER_PROFILE_DIR}/doudian
```

## Persistent profile launcher pattern

Use `launch_persistent_context()` for login-sensitive workflows so cookies/localStorage survive restarts.

```python
#!/usr/bin/env python3
from pathlib import Path
from cloakbrowser import launch_persistent_context

PROFILE_DIR = Path('${CLOAKBROWSER_PROFILE_DIR}/doudian')
PROFILE_DIR.mkdir(parents=True, exist_ok=True)
URL = 'https://fxg.jinritemai.com/ffa/mshop/homepage/index'

ctx = launch_persistent_context(
    str(PROFILE_DIR),
    headless=False,
    humanize=True,
    viewport={'width': 1440, 'height': 900},
    locale='zh-CN',
    timezone='Asia/Shanghai',
)
page = ctx.new_page()
page.goto(URL, wait_until='domcontentloaded', timeout=60000)
print('CloakBrowser opened:', page.title(), page.url, flush=True)
print('Profile:', PROFILE_DIR, flush=True)
print('Press Enter here to close CloakBrowser context.', flush=True)
try:
    input()
finally:
    ctx.close()
```

Run in background with a PTY if the process should stay alive:

```bash
${CLOAKBROWSER_PY} ${CLOAKBROWSER_REPO}/launch_doudian.py
```

## Login handling

If the launched page lands on login, QR, SMS, password, captcha, or device verification, stop and ask the human to complete it in the visible Chromium window. Continue only after the human says login is done.

## Important pitfall

Do not verify CloakBrowser only by looking for an app named `CloakBrowser` in the macOS app list. The running app may show as `Chromium` with bundle id `org.chromium.Chromium`, while the executable path is under `${CLOAKBROWSER_HOME}/.../Chromium.app/...`. Verify by process path and user-data-dir/profile path.

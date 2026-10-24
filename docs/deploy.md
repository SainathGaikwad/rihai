# Deploying Rihai

Three ways to run it, cheapest first. The public URL from option 1 is what goes into outreach emails and the
hackathon submission.

## 1. Streamlit Community Cloud (free, public URL, ~5 minutes)

Deployed on 24 October 2026: **https://rihai-pune.streamlit.app** (app `rihai-pune`, account sainathgaikwad, redeploys on every push to `main`).

Prerequisites: the repo is public on GitHub (`SainathGaikwad/rihai`, branch `main`) and `requirements.txt` is at
the root. Both are already true.

1. Open https://share.streamlit.io and sign in with the **SainathGaikwad** GitHub account.
2. Click **Create app** (or **New app**) and choose **Deploy a public app from GitHub**.
3. Fill in:
   - Repository: `SainathGaikwad/rihai`
   - Branch: `main`
   - Main file path: `rihai/app/streamlit_app.py`
   - App URL: `rihai-pune` (subdomains need 6 to 63 characters), so the address reads `https://rihai-pune.streamlit.app`
4. Click **Advanced settings** only if you want the model layer on:
   - Python version: 3.11 or 3.12
   - Secrets (TOML), one key per line. Paste the real values there and nowhere else:
     ```toml
     RIHAI_LLM_BASE_URL = "https://api.studio.nebius.com/v1"
     RIHAI_LLM_API_KEY = "..."
     RIHAI_LLM_MODEL = "nvidia/Llama-3_3-Nemotron-Super-49B-v1"
     ```
     Without secrets the app runs in template mode, which is the default demo and needs no key at all.
5. Click **Deploy**. First build takes two to three minutes. Every later `git push` to `main` redeploys itself.

If the build fails, the log is on the same page (bottom right, "Manage app"). The two usual causes are a typo in
the main file path and a `requirements.txt` line that cannot be installed; the current file has only
python-dateutil, pandas, streamlit and pytest.

Secrets can be changed later from the app's **Settings > Secrets** without redeploying.

## 2. On a laptop (no internet needed after install)

```
run_rihai.bat                        # Windows: installs requirements once, opens the app in the browser
python -m streamlit run rihai/app/streamlit_app.py
```

For the model layer on a laptop, create `.streamlit/secrets.toml` (git-ignored) with the same three keys, or set
them as environment variables.

## 3. Command line and the agent

```
python -m rihai.agent.run --charges "BNS 303(2)" --custody 2025-01-10 --first-time --lang mr
python -m rihai.agent.run --roster data/samples/roster_sample.csv --out out/
python -m rihai.agent.run --agent --roster data/samples/roster_sample.csv      # Claude Agent SDK harness
```

`--agent` needs `pip install claude-agent-sdk` and an Anthropic key in the environment (`ANTHROPIC_API_KEY`) or a
Claude Code login. The deterministic runs need neither.

## What a deployment must never contain

- a real prison roster, or anything with a prisoner's name: `data/rosters/` is git-ignored and stays on the laptop
- an API key in any committed file; keys go in Streamlit secrets or `.streamlit/secrets.toml`, which is git-ignored
- the phone number of anyone on the team; outreach drafts use `[phone]`

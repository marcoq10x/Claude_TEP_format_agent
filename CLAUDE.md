# Project Notes

## How to Run the App Locally
```
cd ~/Claude_TEP_format_agent
git pull origin main
python3 web/app.py
```
Then open http://127.0.0.1:8080

IMPORTANT: Always use `python3`, NEVER `python`. The command is `python3 web/app.py` from the project root.

## Deployment Workflow
After every feature implementation, always report:
1. Whether all changes are pushed to GitHub
2. Whether a PR needs to be created/merged to `main`
3. Whether Render.com will auto-deploy (it deploys from `main` branch)

## Render.com
- Deploys automatically from `main` branch
- Start command: `gunicorn web.app:app --bind 0.0.0.0:$PORT`
- Build command: `pip install -r requirements.txt`

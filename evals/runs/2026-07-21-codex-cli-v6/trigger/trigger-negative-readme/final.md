There is no `README.md` in the provided workspace, so I couldn’t apply the rewrite directly. The directory only contains [index.html](D:/personal/Vibespec_gate_skill/test%20output/skill-evals/2026-07-21-codex-cli-v6/trigger/trigger-negative-readme/project/index.html:1) and [deployment-evidence.json](D:/personal/Vibespec_gate_skill/test%20output/skill-evals/2026-07-21-codex-cli-v6/trigger/trigger-negative-readme/project/deployment-evidence.json:1), which suggests this is a static site with no install step.

If you want a clearer installation section for this project, this is the version I’d use:

```md
## Installation

This project is a static HTML site. There are no dependencies to install and no build step.

### Run locally

Choose one of the following:

1. Open `index.html` directly in your browser.

2. Serve the project with a local static server:

   ```powershell
   cd project
   python -m http.server 8000
   ```

   Then open `http://localhost:8000` in your browser.

## Requirements

- A modern web browser
- Optional: Python 3, if you want to run a local server
```

If you want me to rewrite the actual README section in place, point me to the real `README.md` or provide its contents.
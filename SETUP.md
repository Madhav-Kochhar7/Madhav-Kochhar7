# Setup instructions

This repo must be named **exactly** `Madhav-Kochhar7` (matching your username) for
GitHub to show it as your profile README.

## 1. Create the repo
- New repo → name it `Madhav-Kochhar7` → public → no README (you already have one here).

## 2. Push these files
```
git init
git remote add origin https://github.com/Madhav-Kochhar7/Madhav-Kochhar7.git
git add .
git commit -m "Initial profile README"
git branch -M main
git push -u origin main
```

## 3. Add a Personal Access Token (for live stats)
The workflow needs a token to query the GitHub API at a higher rate limit
(unauthenticated requests get rate-limited almost immediately).

1. GitHub → Settings → Developer settings → Personal access tokens → **Fine-grained tokens** (or classic).
2. Scopes needed: `read:user`, `repo` (repo only if you want private repos counted).
3. Copy the token.
4. In your `Madhav-Kochhar7` repo → Settings → Secrets and variables → Actions → **New repository secret**.
   - Name: `ACCESS_TOKEN`
   - Value: (paste the token)

## 4. Enable the workflow
- Go to the **Actions** tab → enable workflows if prompted.
- Run "Update profile README stats" manually once (workflow_dispatch) to generate the first real SVGs.
- After that it reruns automatically every day via the cron schedule.

## 5. Editing your info later
All static fields (OS, education, languages, tools, achievements, contact) live at
the top of `today.py` in the `FIELDS` / `CONTACT` dicts — edit those and the next
workflow run (or a manual trigger) regenerates the SVGs automatically.


# GNN Threat Hunter

## Getting Started (For Team Members)

### Step 1 — Fork the repo
Go to [github.com/vaishnaviandom/gnn-threat-hunter](https://github.com/vaishnaviandom/gnn-threat-hunter) and click **Fork** → fork to your personal GitHub account.

### Step 2 — Clone your fork
```bash
git clone git@github.com:YOUR-USERNAME/gnn-threat-hunter.git
cd gnn-threat-hunter
```

### Step 3 — Add the root repo as upstream
```bash
git remote add upstream git@github.com:vaishnaviandom/gnn-threat-hunter.git
```

### Step 4 — Install all dependencies
```bash
chmod +x setup.sh
./setup.sh
```
This automatically sets up Python environments, installs Node modules, and checks the Rust toolchain.

### Step 5 — Set up your environment variables
```bash
cp .env.example .env
```
> The defaults work as-is for local development. No changes needed right now.

### Step 6 — Start the local data layer (requires Docker Desktop running)
```bash
docker compose up -d
```

### Step 7 — Run Django migrations
```bash
cd backend
.venv/bin/python manage.py migrate
```

---

## Daily Workflow

```bash
# Sync with root repo before starting work
git fetch upstream
git merge upstream/main

# Create a branch for your work
git checkout -b feat/your-feature-name

# Push to your fork
git push origin feat/your-feature-name

# Open a Pull Request: your fork → vaishnaviandom/gnn-threat-hunter
```

---

## Requirements
- macOS 12+
- Python 3.11+
- Node.js 18+
- Rust (via [rustup](https://rustup.rs))
- [Docker Desktop](https://www.docker.com/products/docker-desktop)

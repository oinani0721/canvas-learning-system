---
name: deploy-vault
description: Deploy a new Obsidian vault for a course. Use when the user says "/deploy-vault <课程名>" to create, initialize, and switch to a new vault.
license: MIT
metadata:
  author: canvas-learning-system
  version: "1.0"
  story: "Story 1.8 + 1.9"
---

Deploy a new Obsidian vault for a course.

**Input**: Course name (e.g., `/deploy-vault 操作系统`)

**Steps**

1. **Read VAULTS_ROOT from .env**

   ```bash
   grep VAULTS_ROOT .env
   ```

   If `VAULTS_ROOT` is not set or empty, ask the user to configure it first:
   > VAULTS_ROOT is not configured. Please set it in `.env` to the parent directory where you want vaults stored (e.g., `/Users/you/Documents/vaults`).

2. **Create vault directory structure**

   Use the vault name from the user's input. Create the directory under `VAULTS_ROOT`:

   ```bash
   mkdir -p "${VAULTS_ROOT}/<vault-name>"
   mkdir -p "${VAULTS_ROOT}/<vault-name>/.obsidian"
   mkdir -p "${VAULTS_ROOT}/<vault-name>/raw"
   mkdir -p "${VAULTS_ROOT}/<vault-name>/wiki/concepts"
   mkdir -p "${VAULTS_ROOT}/<vault-name>/wiki/canvases"
   mkdir -p "${VAULTS_ROOT}/<vault-name>/outputs/exam_boards"
   ```

3. **Call setup-wizard API** (if backend is running)

   ```bash
   curl -sf -X POST http://localhost:8001/api/v1/system/vault/init \
     -H "Content-Type: application/json" \
     -d '{"vault_path": "${VAULTS_ROOT}/<vault-name>"}'
   ```

   If the backend is not running, skip this step and note it for the user.

4. **Switch backend to new vault**

   ```bash
   curl -sf -X POST http://localhost:8001/api/v1/vault/switch \
     -H "Content-Type: application/json" \
     -d '{"vault_path": "${VAULTS_ROOT}/<vault-name>"}'
   ```

   If the backend is not running, update `.env` and `backend/.env` with the new `ACTIVE_VAULT` value instead.

5. **Output result**

   Report to the user:
   - Vault created at: `${VAULTS_ROOT}/<vault-name>`
   - Backend switched to: `<vault-name>`
   - Obsidian URI: `obsidian://open?vault=<vault-name>`
   - Suggest: "Open the vault in Obsidian with the URI above, or open it manually from Obsidian's vault picker."

**Error Handling**

- If the vault directory already exists, ask the user if they want to switch to it instead of creating a new one.
- If the backend API calls fail, fall back to manual `.env` updates and inform the user to restart Docker.

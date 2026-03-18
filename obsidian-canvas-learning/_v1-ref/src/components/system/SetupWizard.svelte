<script lang="ts">
  /**
   * Canvas Learning System - Setup Wizard
   * Story 1.2: 5-step detection wizard (AC-2, AC-3, AC-4, AC-5, AC-6)
   *
   * Detects: Docker -> Backend API -> Neo4j -> LLM (Ollama) -> LanceDB
   * Shows status lights (green/red/spinner) with fix guidance.
   */

  import type { App } from 'obsidian';
  import type { ApiClient } from '../../services/api-client';
  import type { HealthResponse } from '../../types/api';
  import { DockerService, BACKEND_START_WAIT } from '../../services/docker-service';

  type CheckStatus = 'pending' | 'checking' | 'success' | 'error';

  interface ComponentCheck {
    id: string;
    name: string;
    status: CheckStatus;
    message: string;
    fixAction?: (() => Promise<void>) | null;
    fixLabel?: string;
  }

  let { app, apiClient, onComplete }: {
    app: App;
    apiClient: ApiClient;
    onComplete: () => void;
  } = $props();

  const dockerService = new DockerService();

  let checks: ComponentCheck[] = $state([
    { id: 'docker',  name: 'Docker Desktop',  status: 'pending', message: '等待检测...' },
    { id: 'backend', name: '后端服务 (API)',    status: 'pending', message: '等待检测...' },
    { id: 'neo4j',   name: 'Neo4j 知识图谱',   status: 'pending', message: '等待检测...' },
    { id: 'llm',     name: 'LLM 服务 (Ollama)', status: 'pending', message: '等待检测...' },
    { id: 'lancedb', name: 'LanceDB 向量库',   status: 'pending', message: '等待检测...' },
  ]);

  let isStartingBackend = $state(false);

  let allReady = $derived(checks.every(c => c.status === 'success'));
  let isChecking = $derived(checks.some(c => c.status === 'checking'));

  /**
   * Run all 5 detection steps sequentially.
   * Docker failure cascades to all subsequent steps.
   * Backend failure cascades to Neo4j/LLM/LanceDB.
   */
  async function runAllChecks(): Promise<void> {
    // Reset all to pending first
    for (let i = 0; i < checks.length; i++) {
      checks[i].status = 'pending';
      checks[i].message = '等待检测...';
      checks[i].fixAction = null;
      checks[i].fixLabel = undefined;
    }

    // Step 1: Docker Desktop
    checks[0].status = 'checking';
    checks[0].message = '正在检测 Docker...';

    const dockerRunning = await dockerService.isDockerRunning();
    if (dockerRunning) {
      checks[0].status = 'success';
      checks[0].message = 'Docker Desktop 运行中';
    } else {
      checks[0].status = 'error';
      checks[0].message = '请安装并启动 Docker Desktop';
      // Docker down -> all subsequent checks fail
      for (let i = 1; i < checks.length; i++) {
        checks[i].status = 'error';
        checks[i].message = '需要先启动 Docker Desktop';
      }
      return;
    }

    // Step 2: Backend API
    checks[1].status = 'checking';
    checks[1].message = '正在检测后端服务...';

    let healthData: HealthResponse | null = null;
    try {
      healthData = await apiClient.checkHealth();
    } catch {
      healthData = null;
    }

    if (healthData) {
      checks[1].status = 'success';
      checks[1].message = `后端服务在线 (${healthData.status})`;
    } else {
      checks[1].status = 'error';
      checks[1].message = '后端服务未启动';
      checks[1].fixLabel = '一键启动后端';
      checks[1].fixAction = handleStartBackend;
      // Backend down -> sub-component checks fail
      for (let i = 2; i < checks.length; i++) {
        checks[i].status = 'error';
        checks[i].message = '需要先启动后端服务';
      }
      return;
    }

    // Steps 3-5: Parse component statuses from health response
    const components = healthData.components;

    // Step 3: Neo4j
    checks[2].status = 'checking';
    checks[2].message = '正在检测 Neo4j...';
    const neo4jStatus = components.find(c => c.name === 'neo4j');
    if (neo4jStatus && neo4jStatus.status === 'healthy') {
      checks[2].status = 'success';
      checks[2].message = neo4jStatus.message ?? 'Neo4j 已连接';
    } else {
      checks[2].status = 'error';
      checks[2].message = neo4jStatus?.message ?? 'Neo4j 未就绪，请检查 Docker 容器日志';
    }

    // Step 4: LLM (Ollama)
    checks[3].status = 'checking';
    checks[3].message = '正在检测 LLM 服务...';
    const ollamaStatus = components.find(c => c.name === 'ollama');
    if (ollamaStatus && ollamaStatus.status === 'healthy') {
      checks[3].status = 'success';
      checks[3].message = ollamaStatus.message ?? 'Ollama 服务就绪';
    } else {
      checks[3].status = 'error';
      checks[3].message = ollamaStatus?.message ?? 'Ollama 未就绪，请确认 bge-m3 模型已拉取';
    }

    // Step 5: LanceDB
    checks[4].status = 'checking';
    checks[4].message = '正在检测 LanceDB...';
    const lanceStatus = components.find(c => c.name === 'lancedb');
    if (lanceStatus && lanceStatus.status === 'healthy') {
      checks[4].status = 'success';
      checks[4].message = lanceStatus.message ?? 'LanceDB 就绪';
    } else {
      checks[4].status = 'error';
      checks[4].message = lanceStatus?.message ?? 'LanceDB 未就绪，请检查数据目录权限';
    }
  }

  /**
   * One-click backend start: run docker-compose up -d, then re-check.
   */
  async function handleStartBackend(): Promise<void> {
    isStartingBackend = true;
    checks[1].message = '正在启动后端服务...';
    checks[1].fixAction = null;

    try {
      // Try to find docker-compose.yml
      const vaultPath = (app.vault.adapter as { basePath?: string }).basePath ?? '';
      const composePath = dockerService.findComposePath(vaultPath);

      if (!composePath) {
        checks[1].status = 'error';
        checks[1].message = '未找到 docker-compose.yml，请手动执行 docker-compose up -d';
        checks[1].fixAction = handleStartBackend;
        checks[1].fixLabel = '重试启动';
        isStartingBackend = false;
        return;
      }

      await dockerService.startBackend(composePath);

      // Wait for services to initialize, then re-check
      checks[1].message = `后端启动中，等待服务就绪 (${BACKEND_START_WAIT / 1000}s)...`;
      await new Promise(resolve => setTimeout(resolve, BACKEND_START_WAIT));

      isStartingBackend = false;
      await runAllChecks();
    } catch (err) {
      isStartingBackend = false;
      checks[1].status = 'error';
      checks[1].message = `启动失败: ${err instanceof Error ? err.message : String(err)}`;
      checks[1].fixAction = handleStartBackend;
      checks[1].fixLabel = '重试启动';
    }
  }

  // Auto-run checks on mount
  $effect(() => {
    runAllChecks();
  });
</script>

<div class="cl-sys-wizard">
  <div class="cl-sys-wizard__header">
    <h2 class="cl-sys-wizard__title">Canvas Learning System 安装引导</h2>
    <p class="cl-sys-wizard__subtitle">
      正在检测系统组件，请确保所有服务已启动。
    </p>
  </div>

  <div class="cl-sys-wizard__checks">
    {#each checks as check, i (check.id)}
      <div class="cl-sys-check-row">
        <div class="cl-sys-check-row__indicator">
          {#if check.status === 'checking'}
            <span class="cl-sys-status-dot cl-sys-status-dot--checking"></span>
          {:else if check.status === 'success'}
            <span class="cl-sys-status-dot cl-sys-status-dot--success"></span>
          {:else if check.status === 'error'}
            <span class="cl-sys-status-dot cl-sys-status-dot--error"></span>
          {:else}
            <span class="cl-sys-status-dot cl-sys-status-dot--pending"></span>
          {/if}
        </div>

        <div class="cl-sys-check-row__content">
          <div class="cl-sys-check-row__header">
            <span class="cl-sys-check-row__step">Step {i + 1}</span>
            <span class="cl-sys-check-row__name">{check.name}</span>
          </div>
          <span class="cl-sys-check-row__message" class:cl-sys-check-row__message--error={check.status === 'error'}>
            {check.message}
          </span>
        </div>

        {#if check.fixAction && check.fixLabel}
          <button
            class="cl-sys-check-row__fix-btn"
            onclick={() => check.fixAction?.()}
            disabled={isStartingBackend}
          >
            {isStartingBackend ? '启动中...' : check.fixLabel}
          </button>
        {/if}
      </div>
    {/each}
  </div>

  <div class="cl-sys-wizard__footer">
    {#if allReady}
      <div class="cl-sys-wizard__success">
        <span class="cl-sys-wizard__success-icon">&#10003;</span>
        <span>系统已准备好！</span>
      </div>
      <button class="cl-sys-wizard__complete-btn" onclick={onComplete}>
        创建你的第一个白板
      </button>
    {:else}
      <button
        class="cl-sys-wizard__recheck-btn"
        onclick={() => runAllChecks()}
        disabled={isChecking || isStartingBackend}
      >
        {isChecking ? '检测中...' : '重新检测'}
      </button>
    {/if}
  </div>
</div>

<style>
  /* ═══════════════════════════════════════════════════════════════════════
   * Setup Wizard - Scoped Styles (cl-sys- prefix)
   * Uses Obsidian CSS variables for theme compatibility
   * ═══════════════════════════════════════════════════════════════════════ */

  .cl-sys-wizard {
    display: flex;
    flex-direction: column;
    gap: var(--size-4-4, 16px);
    padding: var(--size-4-4, 16px) var(--size-4-2, 8px);
    max-width: 480px;
    font-family: var(--font-interface);
  }

  /* Header */
  .cl-sys-wizard__header {
    text-align: center;
    padding-bottom: var(--size-4-2, 8px);
    border-bottom: 1px solid var(--background-modifier-border);
  }

  .cl-sys-wizard__title {
    margin: 0 0 var(--size-4-1, 4px) 0;
    font-size: var(--font-ui-large, 1.2em);
    font-weight: 600;
    color: var(--text-normal);
  }

  .cl-sys-wizard__subtitle {
    margin: 0;
    font-size: var(--font-ui-small, 0.85em);
    color: var(--text-muted);
  }

  /* Check rows */
  .cl-sys-wizard__checks {
    display: flex;
    flex-direction: column;
  }

  .cl-sys-check-row {
    display: flex;
    align-items: center;
    gap: var(--size-4-2, 8px);
    padding: var(--size-4-2, 8px) 0;
    border-bottom: 1px solid var(--background-modifier-border);
  }

  .cl-sys-check-row:last-child {
    border-bottom: none;
  }

  .cl-sys-check-row__indicator {
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 20px;
    height: 20px;
  }

  /* Status dots */
  .cl-sys-status-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    display: inline-block;
  }

  .cl-sys-status-dot--success {
    background-color: var(--text-success, #4caf50);
  }

  .cl-sys-status-dot--error {
    background-color: var(--text-error, #f44336);
  }

  .cl-sys-status-dot--pending {
    background-color: var(--text-muted, #999);
  }

  .cl-sys-status-dot--checking {
    width: 10px;
    height: 10px;
    background: transparent;
    border: 2px solid var(--text-muted, #999);
    border-top-color: var(--interactive-accent, #7b6cd9);
    animation: cl-sys-spin 0.8s linear infinite;
  }

  @keyframes cl-sys-spin {
    to { transform: rotate(360deg); }
  }

  /* Check row content */
  .cl-sys-check-row__content {
    flex: 1;
    min-width: 0;
  }

  .cl-sys-check-row__header {
    display: flex;
    align-items: center;
    gap: var(--size-4-1, 4px);
    margin-bottom: 2px;
  }

  .cl-sys-check-row__step {
    font-size: var(--font-ui-smaller, 0.75em);
    color: var(--text-faint);
    text-transform: uppercase;
    font-weight: 600;
  }

  .cl-sys-check-row__name {
    font-size: var(--font-ui-small, 0.85em);
    font-weight: 500;
    color: var(--text-normal);
  }

  .cl-sys-check-row__message {
    font-size: var(--font-ui-smaller, 0.75em);
    color: var(--text-muted);
  }

  .cl-sys-check-row__message--error {
    color: var(--text-error, #f44336);
  }

  /* Fix button */
  .cl-sys-check-row__fix-btn {
    flex-shrink: 0;
    padding: var(--size-4-1, 4px) var(--size-4-2, 8px);
    font-size: var(--font-ui-smaller, 0.75em);
    border: 1px solid var(--interactive-accent, #7b6cd9);
    border-radius: var(--radius-s, 4px);
    background: transparent;
    color: var(--interactive-accent, #7b6cd9);
    cursor: pointer;
    transition: background 0.15s ease;
  }

  .cl-sys-check-row__fix-btn:hover:not(:disabled) {
    background: var(--interactive-accent, #7b6cd9);
    color: var(--text-on-accent, #fff);
  }

  .cl-sys-check-row__fix-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  /* Footer */
  .cl-sys-wizard__footer {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--size-4-2, 8px);
    padding-top: var(--size-4-2, 8px);
    border-top: 1px solid var(--background-modifier-border);
  }

  .cl-sys-wizard__success {
    display: flex;
    align-items: center;
    gap: var(--size-4-1, 4px);
    color: var(--text-success, #4caf50);
    font-weight: 600;
    font-size: var(--font-ui-medium, 1em);
  }

  .cl-sys-wizard__success-icon {
    font-size: 1.2em;
  }

  .cl-sys-wizard__complete-btn {
    width: 100%;
    padding: var(--size-4-2, 8px) var(--size-4-4, 16px);
    font-size: var(--font-ui-medium, 1em);
    font-weight: 600;
    border: none;
    border-radius: var(--radius-s, 4px);
    background: var(--interactive-accent, #7b6cd9);
    color: var(--text-on-accent, #fff);
    cursor: pointer;
    transition: background 0.15s ease;
  }

  .cl-sys-wizard__complete-btn:hover {
    background: var(--interactive-accent-hover, #6c5fc7);
  }

  .cl-sys-wizard__recheck-btn {
    padding: var(--size-4-1, 4px) var(--size-4-3, 12px);
    font-size: var(--font-ui-small, 0.85em);
    border: 1px solid var(--background-modifier-border);
    border-radius: var(--radius-s, 4px);
    background: transparent;
    color: var(--text-normal);
    cursor: pointer;
    transition: background 0.15s ease;
  }

  .cl-sys-wizard__recheck-btn:hover:not(:disabled) {
    background: var(--background-modifier-hover, rgba(0,0,0,0.05));
  }

  .cl-sys-wizard__recheck-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style>

import { useState, useEffect, useCallback, useRef } from 'react';
import { ApiClient, type ModelConfigPayload } from '../services/api-client';
import { DockerManager, type DockerStatus } from '../services/docker-manager';
import { BackupManager, type BackupInfo } from '../services/backup-manager';

// ═══════════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════════

interface SettingsData {
  backendUrl: string;
  neo4jUrl: string;
  vaultPath: string;
  chatProvider: string;
  chatModel: string;
  scoringProvider: string;
  scoringModel: string;
}

/** API Keys — persisted in separate localStorage key (AC-6, equivalent to Obsidian data.json) */
interface ApiKeyState {
  chatApiKey: string;
  scoringApiKey: string;
}

interface TestResult {
  status: 'idle' | 'testing' | 'success' | 'error';
  message: string;
}

interface HealthComponent {
  name: string;
  status: string;
  message?: string;
}

type DockerActionStatus = 'idle' | 'running' | 'success' | 'error';

interface DockerState {
  status: DockerStatus;
  message: string;
  actionStatus: DockerActionStatus;
  actionMessage: string;
}

type BackupActionStatus = 'idle' | 'running' | 'success' | 'error';

interface BackupState {
  actionStatus: BackupActionStatus;
  actionMessage: string;
  backups: BackupInfo[];
}

// ═══════════════════════════════════════════════════════════════════════════════
// Constants
// ═══════════════════════════════════════════════════════════════════════════════

const SETTINGS_KEY = 'canvas-learning-settings';
const API_KEYS_KEY = 'canvas-learning-api-keys';
const SECURITY_NOTICE_KEY = 'canvas-learning-security-notice-shown';

const DEFAULT_SETTINGS: SettingsData = {
  backendUrl: 'http://localhost:8001',
  neo4jUrl: 'bolt://localhost:7689',
  vaultPath: '',
  chatProvider: 'gemini',
  chatModel: '',
  scoringProvider: 'gemini',
  scoringModel: '',
};

/** AC-3: Provider dropdown options */
const PROVIDERS = [
  { value: 'gemini', label: 'Google Gemini' },
  { value: 'anthropic', label: 'Anthropic Claude' },
  { value: 'openai', label: 'OpenAI GPT' },
  { value: 'deepseek', label: 'DeepSeek' },
  { value: 'ollama', label: '本地模型 (Ollama/LM Studio)' },
] as const;

/** Per-provider model name placeholders */
const MODEL_PLACEHOLDERS: Record<string, string> = {
  gemini: 'gemini-2.0-flash',
  anthropic: 'claude-3-5-sonnet-20241022',
  openai: 'gpt-4o',
  deepseek: 'deepseek-chat',
  ollama: 'llama3',
};

/**
 * Project root path key in localStorage.
 * User sets this in settings to point to the canvas-learning-system root
 * that contains docker-compose.yml.
 */
const PROJECT_PATH_KEY = 'canvas-learning-project-path';

function loadProjectPath(): string {
  return localStorage.getItem(PROJECT_PATH_KEY) ?? '';
}

function persistProjectPath(path: string): void {
  localStorage.setItem(PROJECT_PATH_KEY, path);
}

/** Singleton DockerManager instance. */
const dockerManager = new DockerManager();

/** Singleton BackupManager instance. */
const backupManager = new BackupManager();

// ═══════════════════════════════════════════════════════════════════════════════
// Persistence
// ═══════════════════════════════════════════════════════════════════════════════

function loadSettings(): SettingsData {
  try {
    const stored = localStorage.getItem(SETTINGS_KEY);
    if (stored) {
      return { ...DEFAULT_SETTINGS, ...JSON.parse(stored) as Partial<SettingsData> };
    }
  } catch {
    // ignore parse errors — use defaults
  }
  return { ...DEFAULT_SETTINGS };
}

function persistSettings(data: SettingsData): void {
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(data));
}

/**
 * AC-6: API Keys stored in local app config.
 * Equivalent to Obsidian's data.json — local-only, never uploaded.
 * Separate key from general settings for clear security boundary.
 */
function loadApiKeys(): ApiKeyState {
  try {
    const stored = localStorage.getItem(API_KEYS_KEY);
    if (stored) {
      const parsed = JSON.parse(stored) as Partial<ApiKeyState>;
      return {
        chatApiKey: parsed.chatApiKey ?? '',
        scoringApiKey: parsed.scoringApiKey ?? '',
      };
    }
  } catch {
    // ignore
  }
  return { chatApiKey: '', scoringApiKey: '' };
}

function persistApiKeys(keys: ApiKeyState): void {
  localStorage.setItem(API_KEYS_KEY, JSON.stringify(keys));
}

// ═══════════════════════════════════════════════════════════════════════════════
// Helpers
// ═══════════════════════════════════════════════════════════════════════════════

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    healthy: 'bg-green-100 text-green-700',
    unhealthy: 'bg-red-100 text-red-700',
    unknown: 'bg-yellow-100 text-yellow-700',
  };
  const dots: Record<string, string> = {
    healthy: 'text-green-500',
    unhealthy: 'text-red-500',
    unknown: 'text-yellow-500',
  };
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${styles[status] ?? 'bg-gray-100 text-gray-600'}`}>
      <span className={dots[status] ?? 'text-gray-400'}>●</span>
      {status}
    </span>
  );
}

function TestFeedback({ result }: { result: TestResult }) {
  if (result.status === 'idle' || result.status === 'testing') return null;
  const cls = result.status === 'success' ? 'text-green-600' : 'text-red-600';
  return <span className={`text-sm ${cls}`}>{result.message}</span>;
}

// ═══════════════════════════════════════════════════════════════════════════════
// Component
// ═══════════════════════════════════════════════════════════════════════════════

interface SettingsProps {
  onBack: () => void;
}

export function Settings({ onBack }: SettingsProps) {
  const [settings, setSettings] = useState<SettingsData>(loadSettings);
  const [apiKeys, setApiKeys] = useState<ApiKeyState>(loadApiKeys);
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveResult, setSaveResult] = useState<{ ok: boolean; msg: string } | null>(null);

  // Health panel
  const [healthLoading, setHealthLoading] = useState(false);
  const [healthComponents, setHealthComponents] = useState<HealthComponent[]>([]);

  // Test results
  const [chatTest, setChatTest] = useState<TestResult>({ status: 'idle', message: '' });
  const [scoringTest, setScoringTest] = useState<TestResult>({ status: 'idle', message: '' });
  const [backendTest, setBackendTest] = useState<TestResult>({ status: 'idle', message: '' });

  // Docker management state
  const [projectPath, setProjectPath] = useState<string>(loadProjectPath);
  const [dockerState, setDockerState] = useState<DockerState>({
    status: 'unknown',
    message: '未检测',
    actionStatus: 'idle',
    actionMessage: '',
  });

  // Backup state
  const [backupState, setBackupState] = useState<BackupState>({
    actionStatus: 'idle',
    actionMessage: '',
    backups: new Array<BackupInfo>(),
  });

  // UI toggles
  const [showChatKey, setShowChatKey] = useState(false);
  const [showScoringKey, setShowScoringKey] = useState(false);
  const [securityNoticeAcked, setSecurityNoticeAcked] = useState(
    () => localStorage.getItem(SECURITY_NOTICE_KEY) === 'true',
  );
  const [showSecurityBanner, setShowSecurityBanner] = useState(false);

  const apiClientRef = useRef<ApiClient | null>(null);

  // Create/update ApiClient when backendUrl changes
  useEffect(() => {
    apiClientRef.current = new ApiClient(settings.backendUrl);
  }, [settings.backendUrl]);

  // Fetch health on mount
  useEffect(() => {
    refreshHealth();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Auto-dismiss save result
  useEffect(() => {
    if (!saveResult) return;
    const t = setTimeout(() => setSaveResult(null), 3000);
    return () => clearTimeout(t);
  }, [saveResult]);

  // ── Field updaters ──────────────────────────────────────────────────

  const updateField = useCallback(
    <K extends keyof SettingsData>(key: K, value: SettingsData[K]) => {
      setSettings((prev) => ({ ...prev, [key]: value }));
      setDirty(true);
      setSaveResult(null);
    },
    [],
  );

  const updateApiKey = useCallback(
    <K extends keyof ApiKeyState>(key: K, value: string) => {
      setApiKeys((prev) => ({ ...prev, [key]: value }));
      setDirty(true);
      setSaveResult(null);
      // AC-6: Show security notice on first API key entry
      if (value.trim() && !securityNoticeAcked) {
        setShowSecurityBanner(true);
        setSecurityNoticeAcked(true);
        localStorage.setItem(SECURITY_NOTICE_KEY, 'true');
      }
    },
    [securityNoticeAcked],
  );

  // ── Health check (AC-2) ─────────────────────────────────────────────

  const refreshHealth = useCallback(async () => {
    setHealthLoading(true);
    const client = apiClientRef.current;

    const offlineComponents: HealthComponent[] = [
      { name: 'Backend API', status: 'unhealthy', message: '不可达' },
      { name: 'Docker', status: 'unknown', message: '未知' },
      { name: 'Neo4j', status: 'unknown' },
      { name: 'LLM API', status: 'unknown' },
      { name: 'LanceDB', status: 'unknown' },
    ];

    if (!client) {
      setHealthComponents(offlineComponents);
      setHealthLoading(false);
      return;
    }

    try {
      const resp = await client.checkHealth();
      if (!resp) {
        setHealthComponents(offlineComponents);
        setHealthLoading(false);
        return;
      }

      // Backend responded → Backend API + Docker are healthy
      const nameMap: Record<string, string> = {
        neo4j: 'Neo4j',
        ollama: 'LLM API',
        lancedb: 'LanceDB',
      };

      const derived: HealthComponent[] = [
        { name: 'Backend API', status: 'healthy', message: 'API 可达' },
        { name: 'Docker', status: 'healthy', message: '容器运行中' },
      ];

      for (const c of resp.components) {
        derived.push({
          name: nameMap[c.name] ?? c.name,
          status: c.status,
          message: c.message ?? undefined,
        });
      }

      setHealthComponents(derived);
    } catch {
      setHealthComponents(offlineComponents);
    } finally {
      setHealthLoading(false);
    }
  }, []);

  // ── Save (AC-8) ────────────────────────────────────────────────────

  const handleSave = useCallback(async () => {
    setSaving(true);
    setSaveResult(null);

    // 1. Persist locally (settings + API keys)
    persistSettings(settings);
    persistApiKeys(apiKeys);

    // 2. Sync to backend
    const client = apiClientRef.current;
    if (!client) {
      setSaveResult({ ok: false, msg: 'ApiClient 未初始化' });
      setSaving(false);
      return;
    }

    const payload: ModelConfigPayload = {
      chatProvider: settings.chatProvider,
      chatModel: settings.chatModel,
      chatApiKey: apiKeys.chatApiKey,
      scoringProvider: settings.scoringProvider,
      scoringModel: settings.scoringModel,
      scoringApiKey: apiKeys.scoringApiKey,
    };

    try {
      const ok = await client.postModelConfig(payload);
      if (ok) {
        setDirty(false);
        setSaveResult({ ok: true, msg: '设置已保存并同步到后端' });
      } else {
        // Local saved, backend sync failed — keep dirty so user can retry
        setSaveResult({ ok: false, msg: '后端同步失败 — 本地已保存' });
      }
    } catch {
      setSaveResult({ ok: false, msg: '后端不可达 — 本地已保存' });
    } finally {
      setSaving(false);
    }
  }, [settings, apiKeys]);

  // ── Test backend connection ─────────────────────────────────────────

  const handleTestBackend = useCallback(async () => {
    setBackendTest({ status: 'testing', message: '连接中...' });
    const client = apiClientRef.current;
    if (!client) {
      setBackendTest({ status: 'error', message: 'Client 未初始化' });
      return;
    }
    try {
      const resp = await client.checkHealth();
      if (resp) {
        setBackendTest({
          status: 'success',
          message: `后端 ${resp.status} (${resp.components.length} 组件)`,
        });
      } else {
        setBackendTest({ status: 'error', message: '后端不可达' });
      }
    } catch (err) {
      setBackendTest({
        status: 'error',
        message: err instanceof Error ? err.message : '连接失败',
      });
    }
  }, []);

  // ── Docker management (Story 1-8) ──────────────────────────────────

  const updateProjectPath = useCallback((value: string) => {
    setProjectPath(value);
    persistProjectPath(value);
  }, []);

  const checkDockerStatus = useCallback(async () => {
    setDockerState((prev) => ({
      ...prev,
      actionStatus: 'running',
      actionMessage: '检测 Docker 状态...',
    }));
    const result = await dockerManager.checkDocker();
    setDockerState((prev) => ({
      ...prev,
      status: result.status,
      message: result.message,
      actionStatus: result.status === 'available' ? 'success' : 'error',
      actionMessage: result.message,
    }));
  }, []);

  // Check Docker status on mount
  useEffect(() => {
    void checkDockerStatus();
  }, [checkDockerStatus]);

  const handleDockerAction = useCallback(
    async (action: 'start' | 'stop' | 'restart') => {
      if (!projectPath.trim()) {
        setDockerState((prev) => ({
          ...prev,
          actionStatus: 'error',
          actionMessage: '请先设置项目根路径（包含 docker-compose.yml 的目录）',
        }));
        return;
      }

      const actionLabels: Record<string, string> = {
        start: '启动',
        stop: '停止',
        restart: '重启',
      };
      const label = actionLabels[action];

      setDockerState((prev) => ({
        ...prev,
        actionStatus: 'running',
        actionMessage: `正在${label}服务...`,
      }));

      let result;
      switch (action) {
        case 'start':
          result = await dockerManager.startServices(projectPath);
          break;
        case 'stop':
          result = await dockerManager.stopServices(projectPath);
          break;
        case 'restart':
          result = await dockerManager.restartServices(projectPath);
          break;
      }

      if (!result.success) {
        setDockerState((prev) => ({
          ...prev,
          actionStatus: 'error',
          actionMessage: `${label}失败: ${result.stderr || '未知错误'}`,
        }));
        return;
      }

      // For start/restart, poll health endpoint (AC-7)
      if (action === 'start' || action === 'restart') {
        setDockerState((prev) => ({
          ...prev,
          actionStatus: 'running',
          actionMessage: '等待后端就绪...',
        }));

        const healthResult = await dockerManager.pollHealthUntilReady(
          settings.backendUrl,
          (_attempt, elapsedMs) => {
            const elapsedSec = Math.round(elapsedMs / 1000);
            setDockerState((prev) => ({
              ...prev,
              actionMessage: `等待后端就绪... (${elapsedSec}s)`,
            }));
          },
        );

        setDockerState((prev) => ({
          ...prev,
          actionStatus: healthResult.ready ? 'success' : 'error',
          actionMessage: healthResult.message,
        }));

        // Refresh health panel after services come up
        if (healthResult.ready) {
          void refreshHealth();
        }
      } else {
        // stop action
        setDockerState((prev) => ({
          ...prev,
          actionStatus: 'success',
          actionMessage: `服务已${label}`,
        }));
        void refreshHealth();
      }
    },
    [projectPath, settings.backendUrl, refreshHealth],
  );

  // ── Backup management (Story 1-8) ────────────────────────────────────

  const loadBackupList = useCallback(async () => {
    if (!projectPath.trim()) return;
    const backups = await backupManager.listBackups(projectPath);
    setBackupState((prev) => ({ ...prev, backups }));
  }, [projectPath]);

  // Load backups when project path changes
  useEffect(() => {
    void loadBackupList();
  }, [loadBackupList]);

  const handleCreateBackup = useCallback(async () => {
    if (!projectPath.trim()) {
      setBackupState((prev) => ({
        ...prev,
        actionStatus: 'error',
        actionMessage: '请先设置项目根路径',
      }));
      return;
    }

    setBackupState((prev) => ({
      ...prev,
      actionStatus: 'running',
      actionMessage: '正在创建备份...',
    }));

    const result = await backupManager.createBackup(projectPath);

    setBackupState((prev) => ({
      ...prev,
      actionStatus: result.success ? 'success' : 'error',
      actionMessage: result.message,
    }));

    // Refresh backup list after creation
    if (result.success) {
      void loadBackupList();
    }
  }, [projectPath, loadBackupList]);

  const handleRestoreBackup = useCallback(
    async (backupPath: string) => {
      if (!projectPath.trim()) return;

      setBackupState((prev) => ({
        ...prev,
        actionStatus: 'running',
        actionMessage: '正在恢复数据...',
      }));

      const result = await backupManager.restoreBackup(
        projectPath,
        backupPath,
        async () => {
          await dockerManager.stopServices(projectPath);
        },
        async () => {
          await dockerManager.startServices(projectPath);
        },
      );

      setBackupState((prev) => ({
        ...prev,
        actionStatus: result.success ? 'success' : 'error',
        actionMessage: result.message,
      }));

      if (result.success) {
        void refreshHealth();
      }
    },
    [projectPath, refreshHealth],
  );

  // ── Test LLM connection (AC-3/AC-4) ─────────────────────────────────

  const testLlm = useCallback(
    async (
      provider: string,
      model: string,
      apiKey: string,
      setResult: (r: TestResult) => void,
    ) => {
      if (!model.trim()) {
        setResult({ status: 'error', message: '请输入模型名称' });
        return;
      }
      if (!apiKey.trim() && provider !== 'ollama') {
        setResult({ status: 'error', message: '请输入 API Key' });
        return;
      }

      setResult({ status: 'testing', message: '测试中...' });
      const client = apiClientRef.current;
      if (!client) {
        setResult({ status: 'error', message: 'Client 未初始化' });
        return;
      }

      try {
        const res = await client.testLlmConnection(provider, model, apiKey);
        if (res.status === 'success') {
          setResult({ status: 'success', message: `连接成功: ${res.model ?? model}` });
        } else {
          setResult({ status: 'error', message: res.error ?? '测试失败' });
        }
      } catch (err) {
        setResult({
          status: 'error',
          message: err instanceof Error ? err.message : '测试失败',
        });
      }
    },
    [],
  );

  // ═══════════════════════════════════════════════════════════════════════
  // Render
  // ═══════════════════════════════════════════════════════════════════════

  return (
    <div className="h-screen bg-gray-50 overflow-y-auto">
      <div className="max-w-2xl mx-auto py-8 px-4">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
            <p className="text-sm text-gray-500 mt-1">
              配置后端连接、LLM 模型和 Vault 路径
            </p>
          </div>
          <button
            onClick={onBack}
            className="px-4 py-2 text-sm text-gray-600 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            &larr; Dashboard
          </button>
        </div>

        {/* AC-6: First-time API key security notice */}
        {showSecurityBanner && (
          <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
            <div className="flex items-start gap-3">
              <span className="text-amber-500 text-lg shrink-0">&#9888;</span>
              <div>
                <p className="text-sm font-medium text-amber-800">安全提示</p>
                <p className="text-sm text-amber-700 mt-1">
                  对话内容会发送给所选 LLM API 供应商。API Key 仅存储在本地应用配置中，不会上传到外部服务。请妥善保管你的 API Key。
                </p>
                <button
                  onClick={() => setShowSecurityBanner(false)}
                  className="mt-2 text-xs text-amber-600 hover:text-amber-800 underline"
                >
                  我已了解
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ── Section 1: System Health (AC-2) ────────────────────────── */}
        <section className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">系统状态</h2>
            <button
              onClick={() => { void refreshHealth(); }}
              disabled={healthLoading}
              className="px-3 py-1.5 text-xs font-medium text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 disabled:opacity-50 transition-colors"
            >
              {healthLoading ? '检测中...' : '重新检测'}
            </button>
          </div>

          {healthComponents.length === 0 && !healthLoading ? (
            <p className="text-sm text-gray-400">加载中...</p>
          ) : (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              {healthComponents.map((c) => (
                <div
                  key={c.name}
                  className="flex items-center gap-2 p-2 bg-gray-50 rounded"
                  title={c.message}
                >
                  <StatusBadge status={c.status} />
                  <span className="text-sm text-gray-700 truncate">{c.name}</span>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* ── Section 2: Chat Model (AC-3) ───────────────────────────── */}
        <section className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-1">对话模型</h2>
          <p className="text-sm text-gray-500 mb-5">用于知识点剖析、解题对话和学习辅导</p>

          {/* Provider dropdown (AC-3) */}
          <div className="mb-4">
            <label htmlFor="chatProvider" className="block text-sm font-medium text-gray-700 mb-1">
              供应商
            </label>
            <select
              id="chatProvider"
              value={settings.chatProvider}
              onChange={(e) => updateField('chatProvider', e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {PROVIDERS.map((p) => (
                <option key={p.value} value={p.value}>{p.label}</option>
              ))}
            </select>
          </div>

          {/* Model name text input (AC-3) */}
          <div className="mb-4">
            <label htmlFor="chatModel" className="block text-sm font-medium text-gray-700 mb-1">
              模型名称
            </label>
            <input
              id="chatModel"
              type="text"
              value={settings.chatModel}
              onChange={(e) => updateField('chatModel', e.target.value)}
              placeholder={MODEL_PLACEHOLDERS[settings.chatProvider] ?? 'model-name'}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
            />
          </div>

          {/* API Key (AC-3, AC-6) */}
          <div className="mb-4">
            <label htmlFor="chatApiKey" className="block text-sm font-medium text-gray-700 mb-1">
              API Key
              {settings.chatProvider === 'ollama' && (
                <span className="text-xs text-gray-400 ml-2">(本地模型无需填写)</span>
              )}
            </label>
            <div className="relative">
              <input
                id="chatApiKey"
                type={showChatKey ? 'text' : 'password'}
                value={apiKeys.chatApiKey}
                onChange={(e) => updateApiKey('chatApiKey', e.target.value)}
                placeholder={settings.chatProvider === 'ollama' ? '本地模型无需 Key' : 'sk-...'}
                autoComplete="off"
                className="w-full px-3 py-2 pr-16 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
              />
              <button
                type="button"
                onClick={() => setShowChatKey((v) => !v)}
                className="absolute right-2 top-1/2 -translate-y-1/2 px-2 py-1 text-xs text-gray-500 hover:text-gray-700"
              >
                {showChatKey ? '隐藏' : '显示'}
              </button>
            </div>
          </div>

          {/* Test Connection (AC-3) */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => testLlm(settings.chatProvider, settings.chatModel, apiKeys.chatApiKey, setChatTest)}
              disabled={chatTest.status === 'testing'}
              className="px-4 py-2 text-sm font-medium text-white bg-indigo-500 rounded-lg hover:bg-indigo-600 disabled:opacity-50 transition-colors"
            >
              {chatTest.status === 'testing' ? '测试中...' : '测试连接'}
            </button>
            <TestFeedback result={chatTest} />
          </div>
        </section>

        {/* ── Section 3: Scoring Model (AC-4) ────────────────────────── */}
        <section className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-1">评分模型</h2>
          <p className="text-sm text-gray-500 mb-5">
            用于 AutoSCORE 评分和知识提取（留空则复用对话模型配置）
          </p>

          <div className="mb-4">
            <label htmlFor="scoringProvider" className="block text-sm font-medium text-gray-700 mb-1">
              供应商
            </label>
            <select
              id="scoringProvider"
              value={settings.scoringProvider}
              onChange={(e) => updateField('scoringProvider', e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {PROVIDERS.map((p) => (
                <option key={p.value} value={p.value}>{p.label}</option>
              ))}
            </select>
          </div>

          <div className="mb-4">
            <label htmlFor="scoringModel" className="block text-sm font-medium text-gray-700 mb-1">
              模型名称
              <span className="text-xs text-gray-400 ml-2">(留空则使用对话模型)</span>
            </label>
            <input
              id="scoringModel"
              type="text"
              value={settings.scoringModel}
              onChange={(e) => updateField('scoringModel', e.target.value)}
              placeholder={MODEL_PLACEHOLDERS[settings.scoringProvider] ?? 'model-name'}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
            />
          </div>

          <div className="mb-4">
            <label htmlFor="scoringApiKey" className="block text-sm font-medium text-gray-700 mb-1">
              API Key
              <span className="text-xs text-gray-400 ml-2">(留空则使用对话模型 Key)</span>
            </label>
            <div className="relative">
              <input
                id="scoringApiKey"
                type={showScoringKey ? 'text' : 'password'}
                value={apiKeys.scoringApiKey}
                onChange={(e) => updateApiKey('scoringApiKey', e.target.value)}
                placeholder="留空则复用对话模型 Key"
                autoComplete="off"
                className="w-full px-3 py-2 pr-16 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
              />
              <button
                type="button"
                onClick={() => setShowScoringKey((v) => !v)}
                className="absolute right-2 top-1/2 -translate-y-1/2 px-2 py-1 text-xs text-gray-500 hover:text-gray-700"
              >
                {showScoringKey ? '隐藏' : '显示'}
              </button>
            </div>
          </div>

          {/* AC-4: Scoring test connection (same structure as chat) */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                // When scoring fields are empty, test with chat model config (fallback)
                const provider = settings.scoringModel ? settings.scoringProvider : settings.chatProvider;
                const model = settings.scoringModel || settings.chatModel;
                const key = apiKeys.scoringApiKey || apiKeys.chatApiKey;
                testLlm(provider, model, key, setScoringTest);
              }}
              disabled={scoringTest.status === 'testing'}
              className="px-4 py-2 text-sm font-medium text-white bg-indigo-500 rounded-lg hover:bg-indigo-600 disabled:opacity-50 transition-colors"
            >
              {scoringTest.status === 'testing' ? '测试中...' : '测试连接'}
            </button>
            <TestFeedback result={scoringTest} />
          </div>
        </section>

        {/* ── Section 4: Embedding (AC-5, read-only) ─────────────────── */}
        <section className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-1">嵌入模型</h2>
          <p className="text-sm text-gray-500 mb-5">用于语义搜索和笔记检索</p>
          <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
            <span className="text-sm font-medium text-gray-700">bge-m3 &middot; Ollama</span>
            <span className="text-xs text-gray-400">(只读，由后端 Docker 管理)</span>
          </div>
        </section>

        {/* ── Section 5: Backend Connection (AC-7) ───────────────────── */}
        <section className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-1">后端连接</h2>
          <p className="text-sm text-gray-500 mb-5">后端服务地址配置</p>

          <div className="mb-4">
            <label htmlFor="backendUrl" className="block text-sm font-medium text-gray-700 mb-1">
              后端 API 地址
            </label>
            <input
              id="backendUrl"
              type="url"
              value={settings.backendUrl}
              onChange={(e) => updateField('backendUrl', e.target.value)}
              placeholder="http://localhost:8001"
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* AC-7: Neo4j URL input */}
          <div className="mb-4">
            <label htmlFor="neo4jUrl" className="block text-sm font-medium text-gray-700 mb-1">
              Neo4j 地址
              <span className="text-xs text-gray-400 ml-2">(仅记录，实际由 Docker 环境变量控制)</span>
            </label>
            <input
              id="neo4jUrl"
              type="text"
              value={settings.neo4jUrl}
              onChange={(e) => updateField('neo4jUrl', e.target.value)}
              placeholder="bolt://localhost:7689"
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
            />
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => { void handleTestBackend(); }}
              disabled={backendTest.status === 'testing'}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-500 rounded-lg hover:bg-blue-600 disabled:opacity-50 transition-colors"
            >
              {backendTest.status === 'testing' ? '测试中...' : '测试后端连接'}
            </button>
            <TestFeedback result={backendTest} />
          </div>
        </section>

        {/* ── Section 6: Vault Path ──────────────────────────────────── */}
        <section className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-1">Obsidian Vault</h2>
          <p className="text-sm text-gray-500 mb-5">用于笔记检索的 Vault 路径</p>
          <label htmlFor="vaultPath" className="block text-sm font-medium text-gray-700 mb-1">
            Vault 路径
          </label>
          <input
            id="vaultPath"
            type="text"
            value={settings.vaultPath}
            onChange={(e) => updateField('vaultPath', e.target.value)}
            placeholder="C:\Users\you\Documents\MyVault"
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
          />
        </section>

        {/* ── Section 7: Docker Management (Story 1-8) ────────────────── */}
        <section className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-1">Docker 服务管理</h2>
          <p className="text-sm text-gray-500 mb-5">管理后端 Docker Compose 服务（Neo4j, Ollama, Backend）</p>

          {/* Project path input */}
          <div className="mb-4">
            <label htmlFor="projectPath" className="block text-sm font-medium text-gray-700 mb-1">
              项目根路径
              <span className="text-xs text-gray-400 ml-2">(包含 docker-compose.yml 的目录)</span>
            </label>
            <input
              id="projectPath"
              type="text"
              value={projectPath}
              onChange={(e) => updateProjectPath(e.target.value)}
              placeholder="C:\Users\you\canvas-learning-system"
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
            />
          </div>

          {/* Docker status badge */}
          <div className="flex items-center gap-2 mb-4">
            <span className="text-sm font-medium text-gray-700">Docker 状态:</span>
            <StatusBadge
              status={
                dockerState.status === 'available'
                  ? 'healthy'
                  : dockerState.status === 'unknown'
                    ? 'unknown'
                    : 'unhealthy'
              }
            />
            <span className="text-sm text-gray-600">{dockerState.message}</span>
            <button
              onClick={() => { void checkDockerStatus(); }}
              className="ml-2 px-2 py-1 text-xs text-gray-500 bg-gray-100 rounded hover:bg-gray-200 transition-colors"
            >
              重新检测
            </button>
          </div>

          {/* Action buttons */}
          <div className="flex gap-3 mb-3">
            <button
              onClick={() => { void handleDockerAction('start'); }}
              disabled={dockerState.actionStatus === 'running' || dockerState.status !== 'available'}
              className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 disabled:opacity-40 transition-colors"
            >
              启动服务
            </button>
            <button
              onClick={() => { void handleDockerAction('restart'); }}
              disabled={dockerState.actionStatus === 'running' || dockerState.status !== 'available'}
              className="px-4 py-2 text-sm font-medium text-white bg-amber-500 rounded-lg hover:bg-amber-600 disabled:opacity-40 transition-colors"
            >
              重启服务
            </button>
            <button
              onClick={() => { void handleDockerAction('stop'); }}
              disabled={dockerState.actionStatus === 'running' || dockerState.status !== 'available'}
              className="px-4 py-2 text-sm font-medium text-white bg-red-500 rounded-lg hover:bg-red-600 disabled:opacity-40 transition-colors"
            >
              停止服务
            </button>
          </div>

          {/* Action status feedback */}
          {dockerState.actionMessage && (
            <div
              className={`text-sm mt-2 ${
                dockerState.actionStatus === 'error'
                  ? 'text-red-600'
                  : dockerState.actionStatus === 'success'
                    ? 'text-green-600'
                    : 'text-blue-600'
              }`}
            >
              {dockerState.actionStatus === 'running' && (
                <span className="inline-block animate-pulse mr-1">&#9679;</span>
              )}
              {dockerState.actionMessage}
            </div>
          )}
        </section>

        {/* ── Section 8: Data Management (Story 1-8) ───────────────────── */}
        <section className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-1">数据管理</h2>
          <p className="text-sm text-gray-500 mb-5">备份和索引管理</p>

          <div className="flex gap-3 mb-4">
            <button
              onClick={() => { void handleCreateBackup(); }}
              disabled={backupState.actionStatus === 'running' || !projectPath.trim()}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-40 transition-colors"
            >
              {backupState.actionStatus === 'running' ? '备份中...' : '手动备份'}
            </button>
            <button
              disabled
              className="px-4 py-2 text-sm font-medium text-gray-400 bg-gray-100 rounded-lg cursor-not-allowed"
              title="Story 2.7"
            >
              重建索引
            </button>
          </div>

          {/* Backup action feedback */}
          {backupState.actionMessage && (
            <div
              className={`text-sm mb-4 ${
                backupState.actionStatus === 'error'
                  ? 'text-red-600'
                  : backupState.actionStatus === 'success'
                    ? 'text-green-600'
                    : 'text-blue-600'
              }`}
            >
              {backupState.actionStatus === 'running' && (
                <span className="inline-block animate-pulse mr-1">&#9679;</span>
              )}
              {backupState.actionMessage}
            </div>
          )}

          {/* Backup list */}
          {backupState.backups.length > 0 && (
            <div className="mt-3">
              <h3 className="text-sm font-medium text-gray-700 mb-2">
                已有备份 ({backupState.backups.length})
              </h3>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {backupState.backups.map((backup) => (
                  <div
                    key={backup.name}
                    className="flex items-center justify-between p-2 bg-gray-50 rounded"
                  >
                    <div>
                      <span className="text-sm font-mono text-gray-700">
                        {backup.name}
                      </span>
                      <span className="text-xs text-gray-400 ml-2">
                        {new Date(backup.createdAt).toLocaleString()}
                      </span>
                    </div>
                    <button
                      onClick={() => { void handleRestoreBackup(backup.path); }}
                      disabled={backupState.actionStatus === 'running'}
                      className="px-3 py-1 text-xs font-medium text-amber-700 bg-amber-50 border border-amber-200 rounded hover:bg-amber-100 disabled:opacity-40 transition-colors"
                    >
                      恢复
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>

        {/* ── Save Bar ──────────────────────────────────────────────── */}
        <div className="flex items-center justify-end gap-3 pb-8">
          {saveResult && (
            <span className={`text-sm font-medium ${saveResult.ok ? 'text-green-600' : 'text-amber-600'}`}>
              {saveResult.msg}
            </span>
          )}
          <button
            onClick={() => { void handleSave(); }}
            disabled={!dirty || saving}
            className="px-6 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-40 transition-colors"
          >
            {saving ? '保存中...' : '保存设置'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// Exported helpers (used by other modules)
// ═══════════════════════════════════════════════════════════════════════════════

export function getStoredSettings(): SettingsData {
  return loadSettings();
}

export type { SettingsData };

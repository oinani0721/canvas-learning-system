/**
 * Canvas Learning System - Settings Page
 * Story 1.3: Model Configuration & System Settings Panel
 *
 * Main settings page with tabbed layout containing 6 configuration sections:
 *   1. System Health Status (always visible at top)
 *   2. Chat Model (Models tab)
 *   3. Scoring Model (Models tab)
 *   4. Embedding Model - read-only (Models tab)
 *   5. Backend Connection (Connection tab)
 *   6. Data Management (Data tab)
 *
 * Uses shadcn/ui Tabs component for section navigation.
 * All settings are persisted locally via Tauri Store / localStorage.
 *
 * [Source: Story 1.3 AC-1 — settings panel with 6 config areas]
 * [Source: Story 1.3 AC-8 — model config synced to backend]
 */

import { MessageSquare, GraduationCap, Settings } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useSettings } from "@/hooks/use-settings";
import { SystemHealthPanel } from "./system-health-panel";
import { ModelConfigSection } from "./model-config-section";
import { EmbeddingStatusSection } from "./embedding-status-section";
import { BackendConnectionSection } from "./backend-connection-section";
import { DataManagementSection } from "./data-management-section";
import { UsageStatisticsSection } from "./usage-statistics-section";

export function SettingsPage() {
  const { settings, loading, updateSettings } = useSettings();

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-[var(--muted-foreground)]">
          Loading settings...
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-6">
      {/* Page header */}
      <div className="flex items-center gap-3">
        <Settings className="h-7 w-7 text-[var(--primary)]" />
        <div>
          <h1 className="text-2xl font-bold">Settings</h1>
          <p className="text-sm text-[var(--muted-foreground)]">
            Configure LLM models, connections, and system preferences
          </p>
        </div>
      </div>

      {/* System Health — always visible at top (AC-2) */}
      <SystemHealthPanel />

      {/* Tabbed sections */}
      <Tabs defaultValue="models" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="models">Models</TabsTrigger>
          <TabsTrigger value="connection">Connection</TabsTrigger>
          <TabsTrigger value="data">Data</TabsTrigger>
          <TabsTrigger value="usage">Usage</TabsTrigger>
        </TabsList>

        {/* Models tab — Chat + Scoring + Embedding */}
        <TabsContent value="models" className="space-y-4">
          {/* Chat Model (AC-3) */}
          <ModelConfigSection
            title="Chat Model"
            description="Model used for Agent conversations with you"
            icon={
              <MessageSquare className="h-5 w-5 text-[var(--ctp-blue)]" />
            }
            provider={settings.chatProvider}
            modelName={settings.chatModel}
            apiKey={settings.chatApiKey}
            apiKeyNoticeShown={settings.apiKeyNoticeShown}
            onProviderChange={(val) =>
              updateSettings({ chatProvider: val })
            }
            onModelNameChange={(val) =>
              updateSettings({ chatModel: val })
            }
            onApiKeyChange={(val) =>
              updateSettings({ chatApiKey: val })
            }
            onApiKeyNoticeShown={() =>
              updateSettings({ apiKeyNoticeShown: true })
            }
          />

          {/* Scoring Model (AC-4) */}
          <ModelConfigSection
            title="Scoring Model"
            description="Model used for AutoSCORE grading and knowledge extraction (independent from chat)"
            icon={
              <GraduationCap className="h-5 w-5 text-[var(--ctp-green)]" />
            }
            provider={settings.scoringProvider}
            modelName={settings.scoringModel}
            apiKey={settings.scoringApiKey}
            apiKeyNoticeShown={settings.apiKeyNoticeShown}
            onProviderChange={(val) =>
              updateSettings({ scoringProvider: val })
            }
            onModelNameChange={(val) =>
              updateSettings({ scoringModel: val })
            }
            onApiKeyChange={(val) =>
              updateSettings({ scoringApiKey: val })
            }
            onApiKeyNoticeShown={() =>
              updateSettings({ apiKeyNoticeShown: true })
            }
          />

          {/* Embedding Model - read only (AC-5) */}
          <EmbeddingStatusSection />
        </TabsContent>

        {/* Connection tab — Backend + Neo4j */}
        <TabsContent value="connection" className="space-y-4">
          <BackendConnectionSection
            backendUrl={settings.backendUrl}
            neo4jUrl={settings.neo4jUrl}
            onBackendUrlChange={(val) =>
              updateSettings({ backendUrl: val })
            }
            onNeo4jUrlChange={(val) =>
              updateSettings({ neo4jUrl: val })
            }
          />
        </TabsContent>

        {/* Data tab — Backup + Rebuild Index */}
        <TabsContent value="data" className="space-y-4">
          <DataManagementSection />
        </TabsContent>

        {/* Usage tab — LLM token & cost tracking (Story 3.12) */}
        <TabsContent value="usage" className="space-y-4">
          <UsageStatisticsSection />
        </TabsContent>
      </Tabs>
    </div>
  );
}

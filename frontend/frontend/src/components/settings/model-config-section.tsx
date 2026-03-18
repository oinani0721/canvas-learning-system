/**
 * Canvas Learning System - Model Configuration Section
 * Story 1.3 AC-3/AC-4: Chat and Scoring model configuration
 *
 * Reusable component for configuring an LLM model:
 *   - Provider dropdown (Gemini / Claude / GPT / Ollama)
 *   - Model name text input with placeholder hints
 *   - API Key password input with show/hide toggle
 *   - "Test Connection" button with success/failure feedback
 *
 * [Source: Story 1.3 Task 3 / Task 4 — model config UI]
 * [Source: Story 1.3 AC-6 — API Key password type + toggle + first-time notice]
 */

import { useCallback, useState } from "react";
import { Eye, EyeOff, Loader2, CheckCircle2, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { getApiClient } from "@/lib/api-client";
import type { LLMProvider } from "@/types/settings";

/** Provider display labels. */
const PROVIDER_OPTIONS: { value: LLMProvider; label: string }[] = [
  { value: "gemini", label: "Google Gemini" },
  { value: "anthropic", label: "Anthropic Claude" },
  { value: "openai", label: "OpenAI GPT" },
  { value: "ollama", label: "Local (Ollama / LM Studio)" },
];

/** Placeholder hints per provider. */
const MODEL_PLACEHOLDERS: Record<LLMProvider, string> = {
  gemini: "gemini-2.0-flash",
  anthropic: "claude-3-5-sonnet-20241022",
  openai: "gpt-4o",
  ollama: "llama3",
};

interface ModelConfigSectionProps {
  /** Section title (e.g. "Chat Model", "Scoring Model"). */
  title: string;
  /** Section description. */
  description: string;
  /** Icon component to display next to the title. */
  icon: React.ReactNode;
  /** Current provider value. */
  provider: LLMProvider;
  /** Current model name. */
  modelName: string;
  /** Current API key. */
  apiKey: string;
  /** Whether the first-time security notice has been shown. */
  apiKeyNoticeShown: boolean;
  /** Callback when provider changes. */
  onProviderChange: (value: LLMProvider) => void;
  /** Callback when model name changes. */
  onModelNameChange: (value: string) => void;
  /** Callback when API key changes. */
  onApiKeyChange: (value: string) => void;
  /** Callback to mark the security notice as shown. */
  onApiKeyNoticeShown: () => void;
}

type TestState =
  | { status: "idle" }
  | { status: "testing" }
  | { status: "success"; model: string }
  | { status: "failed"; error: string };

export function ModelConfigSection({
  title,
  description,
  icon,
  provider,
  modelName,
  apiKey,
  apiKeyNoticeShown,
  onProviderChange,
  onModelNameChange,
  onApiKeyChange,
  onApiKeyNoticeShown,
}: ModelConfigSectionProps) {
  const [showApiKey, setShowApiKey] = useState(false);
  const [testState, setTestState] = useState<TestState>({ status: "idle" });
  const [showNotice, setShowNotice] = useState(false);

  /** Handle API key change with first-time security notice (AC-6). */
  const handleApiKeyChange = useCallback(
    (value: string) => {
      if (!apiKeyNoticeShown && value.length > 0) {
        setShowNotice(true);
        onApiKeyNoticeShown();
      }
      onApiKeyChange(value);
    },
    [apiKeyNoticeShown, onApiKeyChange, onApiKeyNoticeShown]
  );

  /** Test LLM connection via the backend (AC-3). */
  const handleTestConnection = useCallback(async () => {
    setTestState({ status: "testing" });

    const client = getApiClient();
    const result = await client.testLlmConnection(
      provider,
      modelName,
      apiKey
    );

    if (result.status === "success") {
      setTestState({ status: "success", model: result.model ?? modelName });
    } else {
      setTestState({
        status: "failed",
        error: result.error ?? "Connection failed",
      });
    }
  }, [provider, modelName, apiKey]);

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          {icon}
          <CardTitle className="text-lg">{title}</CardTitle>
        </div>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Provider dropdown */}
        <div className="space-y-2">
          <Label htmlFor={`${title}-provider`}>Provider</Label>
          <Select
            value={provider}
            onValueChange={(val) => onProviderChange(val as LLMProvider)}
          >
            <SelectTrigger id={`${title}-provider`} className="w-full">
              <SelectValue placeholder="Select provider" />
            </SelectTrigger>
            <SelectContent>
              {PROVIDER_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Model name */}
        <div className="space-y-2">
          <Label htmlFor={`${title}-model`}>Model Name</Label>
          <Input
            id={`${title}-model`}
            placeholder={MODEL_PLACEHOLDERS[provider] ?? ""}
            value={modelName}
            onChange={(e) => onModelNameChange(e.target.value)}
          />
          <p className="text-xs text-[var(--muted-foreground)]">
            Model identifier sent to the provider
          </p>
        </div>

        {/* API Key with show/hide toggle */}
        <div className="space-y-2">
          <Label htmlFor={`${title}-apikey`}>API Key</Label>
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Input
                id={`${title}-apikey`}
                type={showApiKey ? "text" : "password"}
                placeholder="sk-..."
                value={apiKey}
                onChange={(e) => handleApiKeyChange(e.target.value)}
                className="pr-10"
              />
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                onClick={() => setShowApiKey(!showApiKey)}
              >
                {showApiKey ? (
                  <EyeOff className="h-4 w-4 text-[var(--muted-foreground)]" />
                ) : (
                  <Eye className="h-4 w-4 text-[var(--muted-foreground)]" />
                )}
              </Button>
            </div>
          </div>
          <p className="text-xs text-[var(--muted-foreground)]">
            Stored locally only, never sent to logs
          </p>
        </div>

        {/* Security notice (shown once on first API key input) */}
        {showNotice && (
          <div className="rounded-md border border-[var(--status-warning)]/30 bg-[var(--status-warning)]/10 px-4 py-3 text-sm">
            <p className="font-medium text-[var(--status-warning)]">
              Security Notice
            </p>
            <p className="mt-1 text-[var(--muted-foreground)]">
              Conversation content will be sent to the selected LLM API
              provider. API keys are stored locally on your device only.
            </p>
            <Button
              variant="ghost"
              size="sm"
              className="mt-2"
              onClick={() => setShowNotice(false)}
            >
              Understood
            </Button>
          </div>
        )}

        {/* Test Connection button + feedback */}
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={handleTestConnection}
            disabled={
              testState.status === "testing" || !modelName
            }
          >
            {testState.status === "testing" ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Testing...
              </>
            ) : (
              "Test Connection"
            )}
          </Button>

          {testState.status === "success" && (
            <span className="flex items-center gap-1 text-sm text-[var(--status-healthy)]">
              <CheckCircle2 className="h-4 w-4" />
              Connected
            </span>
          )}

          {testState.status === "failed" && (
            <span className="flex items-center gap-1 text-sm text-[var(--status-error)]">
              <XCircle className="h-4 w-4" />
              {testState.error}
            </span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

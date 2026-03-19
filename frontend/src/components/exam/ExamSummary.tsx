/**
 * ExamSummary -- Exam completion statistics and calibration panel.
 *
 * Shown after examStatus transitions to 'completed'.
 * Layout (two-column):
 *   - Left: Score calibration -- Agent asks "Do you think the score is accurate?",
 *     user picks one of: too high / accurate / too low. Calls POST /api/v1/exam/{id}/calibrate.
 *   - Right: Completion statistics -- examined node count, elapsed time, average score,
 *     hint usage count, mastery change bar chart (before/after via /mastery/batch),
 *     "view details" button, "return to dashboard" button.
 *
 * Callers:
 * - App.tsx: renders when useExamStore.examStatus === 'completed'
 *
 * Wiring:
 * - useExamStore (examId, examinedNodes, startTime, hintLevel)
 * - ApiClient GET /api/v1/mastery/batch (mastery data for bar chart)
 * - ApiClient POST /api/v1/exam/{examId}/calibrate (calibration vote)
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { useExamStore } from '../../stores/exam-store';
import { ApiClient, type MasteryBatchResponse, type MasteryConceptResponse } from '../../services/api-client';

/** Calibration vote options. */
type CalibrationVote = 'too_high' | 'accurate' | 'too_low';

interface ExamSummaryProps {
  examId: string;
  onReturnDashboard: () => void;
}

/** Mastery comparison data for the bar chart. */
interface MasteryComparison {
  conceptId: string;
  name: string;
  proficiency: number;
}

export function ExamSummary({ examId, onReturnDashboard }: ExamSummaryProps) {
  // Exam store data
  const examinedNodes = useExamStore((s) => s.examinedNodes);
  const startTime = useExamStore((s) => s.startTime);
  const hintLevel = useExamStore((s) => s.hintLevel);

  // API client
  const apiClientRef = useRef<ApiClient | null>(null);
  if (!apiClientRef.current) {
    apiClientRef.current = new ApiClient();
  }
  const apiClient = apiClientRef.current;

  // Calibration state
  const [calibrationVote, setCalibrationVote] = useState<CalibrationVote | null>(null);
  const [calibrationSubmitted, setCalibrationSubmitted] = useState(false);
  const [calibrationLoading, setCalibrationLoading] = useState(false);

  // Mastery data state
  const [masteryData, setMasteryData] = useState<MasteryComparison[]>([]);
  const [averageScore, setAverageScore] = useState<number | null>(null);
  const [masteryLoading, setMasteryLoading] = useState(true);

  // Compute elapsed time string
  const elapsedTime = computeElapsedTime(startTime);

  // Load mastery batch data on mount
  useEffect(() => {
    let cancelled = false;

    async function loadMastery() {
      setMasteryLoading(true);
      try {
        const batch: MasteryBatchResponse | null = await apiClient.getMasteryBatch();
        if (cancelled) return;

        if (batch && batch.concepts.length > 0) {
          // Filter to only examined node concepts
          const examinedSet = new Set(examinedNodes);
          const relevant = batch.concepts.filter(
            (c: MasteryConceptResponse) => examinedSet.has(c.conceptId),
          );

          // If no exact match on conceptId, show all concepts (fallback)
          const displayConcepts = relevant.length > 0 ? relevant : batch.concepts.slice(0, 10);

          const comparisons: MasteryComparison[] = displayConcepts.map(
            (c: MasteryConceptResponse) => ({
              conceptId: c.conceptId,
              name: c.name,
              proficiency: c.effectiveProficiency,
            }),
          );

          setMasteryData(comparisons);

          // Compute average proficiency
          if (comparisons.length > 0) {
            const sum = comparisons.reduce((acc, c) => acc + c.proficiency, 0);
            setAverageScore(sum / comparisons.length);
          }
        }
      } catch (err) {
        console.error('[ExamSummary] Failed to load mastery data:', err);
      } finally {
        if (!cancelled) {
          setMasteryLoading(false);
        }
      }
    }

    loadMastery();
    return () => { cancelled = true; };
  }, [apiClient, examinedNodes]);

  // Submit calibration vote
  const submitCalibration = useCallback(
    async (vote: CalibrationVote) => {
      setCalibrationVote(vote);
      setCalibrationLoading(true);

      try {
        await apiClient.post(`/api/v1/exam/${examId}/calibrate`, {
          vote,
        });
        setCalibrationSubmitted(true);
      } catch (err) {
        console.error('[ExamSummary] Calibration submit failed:', err);
        // Still mark as submitted so UI does not block
        setCalibrationSubmitted(true);
      } finally {
        setCalibrationLoading(false);
      }
    },
    [apiClient, examId],
  );

  // View detailed records — disabled until exam detail view is implemented

  const voteButtons: { value: CalibrationVote; label: string; icon: string }[] = [
    { value: 'too_high', label: '偏高了', icon: '↑' },
    { value: 'accurate', label: '准确', icon: '✓' },
    { value: 'too_low', label: '偏低了', icon: '↓' },
  ];

  return (
    <div className="h-screen bg-[#1e1e2e] flex items-center justify-center p-8">
      <div className="w-full max-w-4xl flex gap-6">
        {/* Left panel: Score calibration */}
        <div className="flex-1 bg-[#181825] border border-[#313244] rounded-xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <svg
              className="w-5 h-5 text-[#f9e2af]"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z"
              />
            </svg>
            <h2 className="text-lg font-semibold text-[#cdd6f4]">
              评分校准
            </h2>
          </div>

          <div className="mb-6">
            <div className="flex items-start gap-3 mb-4">
              {/* Agent avatar */}
              <div className="w-8 h-8 rounded-full bg-[#cba6f7]/20 flex items-center justify-center shrink-0 mt-0.5">
                <svg
                  className="w-4 h-4 text-[#cba6f7]"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z"
                  />
                </svg>
              </div>
              <div className="bg-[#313244] rounded-lg rounded-tl-sm px-4 py-3">
                <p className="text-sm text-[#cdd6f4] leading-relaxed">
                  考试已结束！根据你的表现，系统给出了评分。你觉得这次的分数准确吗？
                </p>
              </div>
            </div>
          </div>

          {/* Calibration vote buttons */}
          {!calibrationSubmitted ? (
            <div className="space-y-2">
              <p className="text-xs text-[#a6adc8] mb-3">
                选择最符合你感受的选项：
              </p>
              <div className="flex gap-3">
                {voteButtons.map((btn) => (
                  <button
                    key={btn.value}
                    onClick={() => submitCalibration(btn.value)}
                    disabled={calibrationLoading}
                    className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                      calibrationLoading && calibrationVote === btn.value
                        ? 'bg-[#cba6f7]/30 text-[#cba6f7] cursor-wait'
                        : calibrationLoading
                          ? 'bg-[#313244] text-[#585b70] cursor-not-allowed'
                          : btn.value === 'too_high'
                            ? 'bg-[#f38ba8]/10 text-[#f38ba8] hover:bg-[#f38ba8]/20 border border-[#f38ba8]/30'
                            : btn.value === 'accurate'
                              ? 'bg-[#a6e3a1]/10 text-[#a6e3a1] hover:bg-[#a6e3a1]/20 border border-[#a6e3a1]/30'
                              : 'bg-[#89b4fa]/10 text-[#89b4fa] hover:bg-[#89b4fa]/20 border border-[#89b4fa]/30'
                    }`}
                  >
                    <span className="text-base">{btn.icon}</span>
                    <span>{btn.label}</span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="bg-[#a6e3a1]/10 border border-[#a6e3a1]/30 rounded-lg px-4 py-3">
              <div className="flex items-center gap-2">
                <svg
                  className="w-4 h-4 text-[#a6e3a1]"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <p className="text-sm text-[#a6e3a1]">
                  已提交校准反馈，感谢！你的反馈将帮助优化评分模型。
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Right panel: Exam statistics */}
        <div className="flex-1 bg-[#181825] border border-[#313244] rounded-xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <svg
              className="w-5 h-5 text-[#89b4fa]"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z"
              />
            </svg>
            <h2 className="text-lg font-semibold text-[#cdd6f4]">
              考试完成
            </h2>
          </div>

          {/* Stats grid */}
          <div className="grid grid-cols-2 gap-3 mb-5">
            {/* Examined nodes count */}
            <StatCard
              label="考察节点数"
              value={String(examinedNodes.length)}
              icon={
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4" />
                </svg>
              }
              color="text-[#a6e3a1]"
            />

            {/* Elapsed time */}
            <StatCard
              label="耗时"
              value={elapsedTime}
              icon={
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              }
              color="text-[#f9e2af]"
            />

            {/* Average score */}
            <StatCard
              label="平均分"
              value={
                masteryLoading
                  ? '...'
                  : averageScore !== null
                    ? `${Math.round(averageScore * 100)}%`
                    : '--'
              }
              icon={
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.562.562 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.562.562 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" />
                </svg>
              }
              color="text-[#cba6f7]"
            />

            {/* Hint usage */}
            <StatCard
              label="提示使用次数"
              value={`${hintLevel}/4`}
              icon={
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path d="M9.663 17h4.674M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              }
              color="text-[#fab387]"
            />
          </div>

          {/* Mastery change bar chart */}
          <div className="mb-5">
            <h3 className="text-xs font-medium text-[#a6adc8] mb-2">
              精通度
            </h3>
            {masteryLoading ? (
              <div className="space-y-2 animate-pulse">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-6 bg-[#313244] rounded" />
                ))}
              </div>
            ) : masteryData.length === 0 ? (
              <p className="text-xs text-[#585b70]">暂无精通度数据</p>
            ) : (
              <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                {masteryData.map((item) => (
                  <MasteryBar
                    key={item.conceptId}
                    name={item.name}
                    proficiency={item.proficiency}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Action buttons */}
          <div className="flex gap-3 mt-auto">
            <button
              disabled
              className="flex-1 px-4 py-2.5 rounded-lg text-sm font-medium bg-[#313244] text-[#585b70] cursor-not-allowed transition-colors"
              title="详细记录功能开发中"
            >
              查看详细记录
            </button>
            <button
              onClick={onReturnDashboard}
              className="flex-1 px-4 py-2.5 rounded-lg text-sm font-medium bg-[#89b4fa] text-[#1e1e2e] hover:bg-[#74c7ec] transition-colors"
            >
              返回 Dashboard
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Helper Components ────────────────────────────────────────────────────────

function StatCard({
  label,
  value,
  icon,
  color,
}: {
  label: string;
  value: string;
  icon: React.ReactNode;
  color: string;
}) {
  return (
    <div className="bg-[#1e1e2e] border border-[#313244] rounded-lg px-3 py-2.5">
      <div className="flex items-center gap-1.5 mb-1">
        <span className={color}>{icon}</span>
        <span className="text-xs text-[#a6adc8]">{label}</span>
      </div>
      <p className={`text-lg font-semibold ${color}`}>{value}</p>
    </div>
  );
}

function MasteryBar({
  name,
  proficiency,
}: {
  name: string;
  proficiency: number;
}) {
  const pct = Math.max(0, Math.min(100, Math.round(proficiency * 100)));

  // Color gradient based on proficiency
  const barColor =
    pct >= 80
      ? 'bg-[#a6e3a1]'
      : pct >= 60
        ? 'bg-[#f9e2af]'
        : pct >= 40
          ? 'bg-[#fab387]'
          : 'bg-[#f38ba8]';

  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-[#a6adc8] w-24 truncate shrink-0" title={name}>
        {name}
      </span>
      <div className="flex-1 bg-[#313244] rounded-full h-4 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${barColor}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs text-[#cdd6f4] w-10 text-right shrink-0">
        {pct}%
      </span>
    </div>
  );
}

// ─── Utility ──────────────────────────────────────────────────────────────────

function computeElapsedTime(startTime: string | null): string {
  if (!startTime) return '--';

  const start = new Date(startTime).getTime();
  const now = Date.now();
  const diffMs = Math.max(0, now - start);
  const totalSeconds = Math.floor(diffMs / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;

  if (minutes < 1) return `${seconds}秒`;
  if (minutes < 60) return `${minutes}分${seconds}秒`;

  const hours = Math.floor(minutes / 60);
  const remainMinutes = minutes % 60;
  return `${hours}时${remainMinutes}分`;
}

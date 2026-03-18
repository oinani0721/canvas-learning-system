/**
 * EdgeGuideTooltip — First-use guide tooltip for edge dialog.
 * Story 4-1 AC-2: Shows "Click to discuss relationship" on first edge creation.
 *
 * Non-modal gray tooltip that auto-dismisses after 2-3 seconds.
 * Guide state persisted in localStorage (shown once per user).
 *
 * Callers:
 * - App.tsx renders this after first edge creation
 */

interface EdgeGuideTooltipProps {
  /** Screen position to render near. */
  position: { x: number; y: number };
  /** Callback when tooltip is dismissed (auto or manual). */
  onDismiss: () => void;
}

export function EdgeGuideTooltip({ position, onDismiss }: EdgeGuideTooltipProps) {
  return (
    <div
      className="fixed z-50 pointer-events-auto animate-fade-in"
      style={{
        left: position.x - 120,
        top: position.y - 50,
      }}
      onClick={onDismiss}
    >
      <div className="bg-gray-700 text-white text-xs px-3 py-2 rounded-lg shadow-lg max-w-60 text-center">
        Click an edge to discuss the relationship between concepts
        <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-gray-700 rotate-45" />
      </div>
    </div>
  );
}

/**
 * InlineAnnotation — 对话内联批注交互组件
 * FR-CONV-05/06: 选中文本 → 浮动工具栏 → 标注面板 → 保存到后端
 *
 * 交互流程：
 * 1. 用户选中对话消息中的文本 → 弹出浮动工具栏（标注/Tips/提问）
 * 2. 点击工具栏按钮 → 展开标注面板（420px宽）
 * 3. 选择Tag类型 + 输入补充说明 + 选择理解度 → 确认保存
 * 4. 已标注文本高亮显示
 *
 * 调用方：
 * - ChatPanel.tsx 在 node 模式下渲染此组件
 *
 * 依赖：
 * - ApiClient.saveTip() — 保存标注到后端
 * - TipItem 类型 — 标注数据结构
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import type { TipItem } from '../../types';
import { ApiClient } from '../../services/api-client';

// ═══════════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════════

interface InlineAnnotationProps {
  /** 当前节点 ID，用于保存标注 */
  nodeId: string;
  /** 拉取到节点的回调（Pull to Node 功能） */
  onPullToNode?: (selectedText: string) => void;
}

/** 标注 Tag 类型 */
type AnnotationTag = 'tips' | 'error' | 'question' | 'keypoint';

/** 理解度级别 */
type UnderstandingLevel = 'understood' | 'fuzzy' | 'not-understood';

/** 浮动工具栏位置 */
interface ToolbarPosition {
  top: number;
  left: number;
}

/** 标注面板状态 */
interface AnnotationPanelState {
  /** 选中的文本 */
  selectedText: string;
  /** 预选的 Tag（从工具栏按钮点击推断） */
  preselectedTag: AnnotationTag;
}

// ═══════════════════════════════════════════════════════════════════════════════
// Constants
// ═══════════════════════════════════════════════════════════════════════════════

const TAG_OPTIONS: { value: AnnotationTag; label: string; color: string }[] = [
  { value: 'tips', label: '💡 Tips', color: 'bg-amber-100 text-amber-800 border-amber-300' },
  { value: 'error', label: '❌ 错误', color: 'bg-red-100 text-red-800 border-red-300' },
  { value: 'question', label: '❓ 提问', color: 'bg-blue-100 text-blue-800 border-blue-300' },
  { value: 'keypoint', label: '📌 关键点', color: 'bg-green-100 text-green-800 border-green-300' },
];

const UNDERSTANDING_OPTIONS: { value: UnderstandingLevel; label: string; color: string }[] = [
  { value: 'understood', label: '已懂', color: 'bg-green-500 text-white' },
  { value: 'fuzzy', label: '模糊', color: 'bg-yellow-500 text-white' },
  { value: 'not-understood', label: '不懂', color: 'bg-red-500 text-white' },
];

// ═══════════════════════════════════════════════════════════════════════════════
// Shared API client
// ═══════════════════════════════════════════════════════════════════════════════

const annotationApiClient = new ApiClient();

// ═══════════════════════════════════════════════════════════════════════════════
// Component
// ═══════════════════════════════════════════════════════════════════════════════

export function InlineAnnotation({ nodeId, onPullToNode }: InlineAnnotationProps) {
  // ── 浮动工具栏状态 ──────────────────────────────────────────────
  const [selectedText, setSelectedText] = useState('');
  const [toolbarPosition, setToolbarPosition] = useState<ToolbarPosition | null>(null);
  const toolbarRef = useRef<HTMLDivElement>(null);

  // ── 标注面板状态 ────────────────────────────────────────────────
  const [panelState, setPanelState] = useState<AnnotationPanelState | null>(null);
  const [activeTag, setActiveTag] = useState<AnnotationTag>('tips');
  const [note, setNote] = useState('');
  const [understanding, setUnderstanding] = useState<UnderstandingLevel>('fuzzy');
  const [isSaving, setIsSaving] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);
  const noteInputRef = useRef<HTMLTextAreaElement>(null);

  // ── 已保存的标注记录（用于高亮） ──────────────────────────────
  const [annotations, setAnnotations] = useState<Array<{
    id: string;
    text: string;
    tag: AnnotationTag;
    understanding: UnderstandingLevel;
  }>>([]);

  // 从 localStorage 加载已有标注
  useEffect(() => {
    const storageKey = `annotations:${nodeId}`;
    const raw = localStorage.getItem(storageKey);
    if (raw) {
      try {
        setAnnotations(JSON.parse(raw));
      } catch {
        setAnnotations([]);
      }
    } else {
      setAnnotations([]);
    }
  }, [nodeId]);

  // ── 隐藏工具栏 ─────────────────────────────────────────────────
  const hideToolbar = useCallback(() => {
    setSelectedText('');
    setToolbarPosition(null);
  }, []);

  // ── 关闭标注面板 ────────────────────────────────────────────────
  const closePanel = useCallback(() => {
    setPanelState(null);
    setNote('');
    setUnderstanding('fuzzy');
    hideToolbar();
  }, [hideToolbar]);

  // ── 监听文本选中事件 ────────────────────────────────────────────
  useEffect(() => {
    function handleSelectionChange() {
      // 如果标注面板已打开，不更新工具栏
      if (panelState) return;

      const selection = window.getSelection();
      if (!selection || selection.isCollapsed || !selection.toString().trim()) {
        return;
      }

      const text = selection.toString().trim();
      if (!text) return;

      // 仅当选区在 chat message 容器内才激活
      const anchorNode = selection.anchorNode;
      if (!anchorNode) return;
      const parentEl =
        anchorNode instanceof HTMLElement ? anchorNode : anchorNode.parentElement;
      if (!parentEl?.closest('[data-chat-message]')) return;

      const range = selection.getRangeAt(0);
      const rect = range.getBoundingClientRect();

      setSelectedText(text);
      setToolbarPosition({
        top: rect.top + window.scrollY - 48,
        left: rect.left + window.scrollX + rect.width / 2,
      });
    }

    document.addEventListener('selectionchange', handleSelectionChange);
    return () => document.removeEventListener('selectionchange', handleSelectionChange);
  }, [panelState]);

  // ── 点击外部关闭工具栏（但不关闭面板） ──────────────────────────
  useEffect(() => {
    function handleMouseDown(e: MouseEvent) {
      const target = e.target as HTMLElement;

      // 如果点击在工具栏或面板内，不关闭
      if (toolbarRef.current?.contains(target)) return;
      if (panelRef.current?.contains(target)) return;

      // 如果面板打开中，只在点击面板外部时关闭面板
      if (panelState) {
        requestAnimationFrame(() => {
          closePanel();
        });
        return;
      }

      // 工具栏模式：延迟检查选区是否还在
      requestAnimationFrame(() => {
        const sel = window.getSelection();
        if (!sel || sel.isCollapsed) {
          hideToolbar();
        }
      });
    }

    document.addEventListener('mousedown', handleMouseDown);
    return () => document.removeEventListener('mousedown', handleMouseDown);
  }, [hideToolbar, closePanel, panelState]);

  // ── 打开标注面板 ────────────────────────────────────────────────
  const openPanel = useCallback((preselectedTag: AnnotationTag) => {
    if (!selectedText) return;

    setPanelState({
      selectedText,
      preselectedTag,
    });
    setActiveTag(preselectedTag);
    setNote('');
    setUnderstanding('fuzzy');

    // 聚焦到备注输入框
    requestAnimationFrame(() => {
      noteInputRef.current?.focus();
    });
  }, [selectedText]);

  // ── 确认保存标注 ────────────────────────────────────────────────
  const handleSave = useCallback(async () => {
    if (!panelState) return;

    setIsSaving(true);

    // 构建标注内容：tag + 理解度 + 备注
    const tagLabel = TAG_OPTIONS.find((t) => t.value === activeTag)?.label ?? activeTag;
    const understandingLabel = UNDERSTANDING_OPTIONS.find((u) => u.value === understanding)?.label ?? understanding;
    const fullContent = [
      `[${tagLabel}]`,
      panelState.selectedText,
      note ? `备注：${note}` : '',
      `理解度：${understandingLabel}`,
    ].filter(Boolean).join('\n');

    // 构建 tags 数组
    const tags = [activeTag, `understanding:${understanding}`];

    // 保存到 localStorage（即时、离线安全）
    const storageKey = `tips:${nodeId}`;
    const existing: TipItem[] = JSON.parse(localStorage.getItem(storageKey) || '[]');
    const newTip: TipItem = {
      tipId: crypto.randomUUID(),
      content: fullContent,
      category: activeTag,
      annotatedAt: new Date().toISOString(),
      contextMessages: [],
    };
    localStorage.setItem(storageKey, JSON.stringify([...existing, newTip]));

    // 保存标注记录（用于高亮显示）
    const annotationRecord = {
      id: newTip.tipId,
      text: panelState.selectedText,
      tag: activeTag,
      understanding,
    };
    const updatedAnnotations = [...annotations, annotationRecord];
    setAnnotations(updatedAnnotations);
    localStorage.setItem(`annotations:${nodeId}`, JSON.stringify(updatedAnnotations));

    // 异步 POST 到后端 — saveTip 真实 API
    annotationApiClient.saveTip(nodeId, fullContent, tags).catch(() => {
      // 静默忽略 — localStorage 已有数据
    });

    // 高亮已标注文本
    applyHighlight(panelState.selectedText, activeTag);

    setIsSaving(false);

    // 清除选区并关闭面板
    window.getSelection()?.removeAllRanges();
    closePanel();
  }, [panelState, activeTag, note, understanding, nodeId, annotations, closePanel]);

  // ── 高亮已标注文本 ──────────────────────────────────────────────
  const applyHighlight = useCallback((text: string, tag: AnnotationTag) => {
    // 在所有 chat message 容器中查找并高亮匹配文本
    const messageEls = document.querySelectorAll('[data-chat-message]');

    const colorMap: Record<AnnotationTag, string> = {
      tips: 'rgba(251, 191, 36, 0.25)',
      error: 'rgba(239, 68, 68, 0.25)',
      question: 'rgba(59, 130, 246, 0.25)',
      keypoint: 'rgba(34, 197, 94, 0.25)',
    };

    messageEls.forEach((msgEl) => {
      const walker = document.createTreeWalker(
        msgEl,
        NodeFilter.SHOW_TEXT,
        null,
      );

      let node: Text | null;
      while ((node = walker.nextNode() as Text | null)) {
        const idx = node.textContent?.indexOf(text) ?? -1;
        if (idx === -1) continue;

        const range = document.createRange();
        range.setStart(node, idx);
        range.setEnd(node, idx + text.length);

        const mark = document.createElement('mark');
        mark.className = 'inline-annotation-highlight';
        mark.style.backgroundColor = colorMap[tag];
        mark.style.borderRadius = '2px';
        mark.style.padding = '0 1px';
        mark.title = `${TAG_OPTIONS.find((t) => t.value === tag)?.label ?? tag}`;

        try {
          range.surroundContents(mark);
        } catch {
          // 如果跨节点选区无法 surroundContents，跳过
        }
        break; // 每条消息只高亮第一个匹配
      }
    });
  }, []);

  // ── 页面加载时恢复已有标注的高亮 ────────────────────────────────
  useEffect(() => {
    // 用 MutationObserver 等待消息渲染完成后再应用高亮
    if (annotations.length === 0) return;

    const timer = setTimeout(() => {
      annotations.forEach((ann) => {
        applyHighlight(ann.text, ann.tag);
      });
    }, 500);

    return () => clearTimeout(timer);
  }, [annotations, applyHighlight]);

  // ── Pull to Node ─────────────────────────────────────────────────
  const handlePullToNode = useCallback(() => {
    if (!selectedText || !onPullToNode) return;
    onPullToNode(selectedText);
    window.getSelection()?.removeAllRanges();
    hideToolbar();
  }, [selectedText, onPullToNode, hideToolbar]);

  // ── Esc 键关闭面板 ──────────────────────────────────────────────
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        if (panelState) {
          closePanel();
        } else if (toolbarPosition) {
          hideToolbar();
        }
      }
    }

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [panelState, toolbarPosition, closePanel, hideToolbar]);

  // ═══════════════════════════════════════════════════════════════════════════
  // Render: 浮动工具栏
  // ═══════════════════════════════════════════════════════════════════════════

  if (panelState) {
    // 标注面板（420px宽，固定在消息区域右侧）
    return (
      <div
        ref={panelRef}
        className="fixed z-[9999] w-[420px] rounded-xl bg-white shadow-2xl border border-gray-200 overflow-hidden"
        style={{
          top: toolbarPosition ? Math.max(toolbarPosition.top - 40, 60) : 100,
          left: toolbarPosition
            ? Math.min(toolbarPosition.left - 210, window.innerWidth - 440)
            : 100,
        }}
      >
        {/* 面板头部 */}
        <div className="flex items-center justify-between px-4 py-3 bg-gray-50 border-b border-gray-200">
          <h4 className="text-sm font-semibold text-gray-800">添加标注</h4>
          <button
            type="button"
            onClick={closePanel}
            className="text-gray-400 hover:text-gray-600 transition-colors text-lg leading-none"
            aria-label="关闭标注面板"
          >
            &times;
          </button>
        </div>

        {/* 选中文本预览 */}
        <div className="px-4 py-3 bg-gray-50/50 border-b border-gray-100">
          <p className="text-xs text-gray-500 mb-1">选中内容</p>
          <p className="text-sm text-gray-700 leading-relaxed line-clamp-3 italic">
            &ldquo;{panelState.selectedText}&rdquo;
          </p>
        </div>

        <div className="px-4 py-3 space-y-4">
          {/* Tag 类型选择器 */}
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-2">
              标注类型
            </label>
            <div className="flex flex-wrap gap-2">
              {TAG_OPTIONS.map((tag) => (
                <button
                  key={tag.value}
                  type="button"
                  onClick={() => setActiveTag(tag.value)}
                  className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-all ${
                    activeTag === tag.value
                      ? `${tag.color} ring-2 ring-offset-1 ring-gray-300`
                      : 'bg-gray-50 text-gray-500 border-gray-200 hover:bg-gray-100'
                  }`}
                >
                  {tag.label}
                </button>
              ))}
            </div>
          </div>

          {/* 补充说明输入框 */}
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-2">
              补充说明 <span className="text-gray-400">（可选）</span>
            </label>
            <textarea
              ref={noteInputRef}
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="写下你的想法或疑问..."
              rows={3}
              className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent placeholder:text-gray-300"
            />
          </div>

          {/* 理解度选择 */}
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-2">
              理解程度
            </label>
            <div className="flex gap-2">
              {UNDERSTANDING_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setUnderstanding(opt.value)}
                  className={`flex-1 py-2 rounded-lg text-xs font-medium transition-all ${
                    understanding === opt.value
                      ? `${opt.color} shadow-sm ring-2 ring-offset-1 ring-gray-300`
                      : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* 操作按钮 */}
        <div className="flex items-center justify-end gap-2 px-4 py-3 bg-gray-50 border-t border-gray-200">
          <button
            type="button"
            onClick={closePanel}
            className="px-4 py-2 text-xs font-medium text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          >
            取消
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={isSaving}
            className="px-5 py-2 text-xs font-medium text-white bg-blue-500 hover:bg-blue-600 rounded-lg shadow-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSaving ? '保存中...' : '确认标注'}
          </button>
        </div>
      </div>
    );
  }

  // 浮动工具栏
  if (!toolbarPosition || !selectedText) return null;

  return (
    <div
      ref={toolbarRef}
      role="toolbar"
      aria-label="内联标注工具栏"
      className="fixed z-[9999] flex items-center gap-0.5 rounded-lg bg-gray-900 px-1 py-1 shadow-lg"
      style={{
        top: toolbarPosition.top,
        left: toolbarPosition.left,
        transform: 'translateX(-50%)',
      }}
    >
      <button
        type="button"
        onClick={() => openPanel('keypoint')}
        className="rounded px-2.5 py-1.5 text-xs font-medium text-gray-100 transition-colors hover:bg-gray-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
        title="标注为关键点"
      >
        📌 标注
      </button>

      <span className="h-4 w-px bg-gray-600" aria-hidden="true" />

      <button
        type="button"
        onClick={() => openPanel('tips')}
        className="rounded px-2.5 py-1.5 text-xs font-medium text-gray-100 transition-colors hover:bg-gray-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
        title="添加 Tips 备注"
      >
        💡 Tips
      </button>

      <span className="h-4 w-px bg-gray-600" aria-hidden="true" />

      <button
        type="button"
        onClick={() => openPanel('question')}
        className="rounded px-2.5 py-1.5 text-xs font-medium text-gray-100 transition-colors hover:bg-gray-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
        title="标注为疑问"
      >
        ❓ 提问
      </button>

      <span className="h-4 w-px bg-gray-600" aria-hidden="true" />

      <button
        type="button"
        onClick={handlePullToNode}
        disabled={!onPullToNode}
        className="rounded px-2.5 py-1.5 text-xs font-medium text-gray-100 transition-colors hover:bg-gray-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 disabled:cursor-not-allowed disabled:opacity-40"
        title="拉取到节点"
      >
        拉到节点
      </button>

      {/* 箭头指向选区 */}
      <span
        aria-hidden="true"
        className="absolute -bottom-1.5 left-1/2 -translate-x-1/2 border-x-[6px] border-t-[6px] border-x-transparent border-t-gray-900"
      />
    </div>
  );
}

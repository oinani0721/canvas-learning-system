"""
BMad Orchestrator CLI - 全自动化开发命令行接口

提供命令:
- epic-develop: 启动 Epic 全自动化工作流
- epic-status: 查看工作流状态
- epic-resume: 恢复中断的工作流
- epic-stop: 停止运行中的工作流

使用方式:
    python -m bmad_orchestrator epic-develop 15 --stories 15.1 15.2 15.3
    python -m bmad_orchestrator epic-status epic-15
    python -m bmad_orchestrator epic-resume epic-15
    python -m bmad_orchestrator epic-stop epic-15

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-11-30
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import List, Literal, Optional

from .graph import compile_graph, resume_workflow, run_epic_workflow

# ============================================================================
# CLI 命令实现
# ============================================================================

async def cmd_epic_develop(
    epic_id: str,
    story_ids: List[str],
    base_path: str,
    worktree_base: Optional[str],
    max_turns: int,
    mode: Optional[Literal["parallel", "linear", "hybrid"]],
    ultrathink: bool,
    dry_run: bool,
    yes: bool = False,
    skip_sm: bool = False,
    skip_po: bool = False,
    skip_analysis: bool = False,
    skip_dev: bool = False,
    skip_qa: bool = False,
    skip_sdd: bool = False,
    resume_from: Optional[str] = None,
    timeout: int = 3600,
    fast_mode: bool = False,
) -> int:
    """
    启动 Epic 全自动化工作流

    Args:
        epic_id: Epic ID
        story_ids: Story IDs
        base_path: 项目根目录
        worktree_base: Worktree 父目录
        max_turns: 最大轮数
        mode: 执行模式
        ultrathink: 启用 UltraThink
        dry_run: 预览模式
        skip_sm: 跳过SM阶段，直接从PO开始
        skip_po: 跳过PO验证阶段
        skip_analysis: 跳过依赖分析阶段
        skip_dev: 跳过DEV阶段，直接从QA开始 (用于re-QA场景)
        skip_qa: 跳过QA审查阶段
        skip_sdd: 跳过SDD验证阶段
        resume_from: 从指定阶段恢复
        timeout: 会话超时时间(秒)
        fast_mode: 快速模式 (跳过PO/QA/SDD)

    Returns:
        退出码 (0=成功, 1=失败)
    """
    # 处理 --resume-from 参数
    if resume_from:
        phase_order = ["sm", "po", "analysis", "dev", "qa", "sdd", "merge", "commit"]
        try:
            resume_index = phase_order.index(resume_from)
            skip_sm = resume_index > 0
            skip_po = resume_index > 1
            skip_analysis = resume_index > 2
            skip_dev = resume_index > 3  # dev=3, qa=4, sdd=5, merge=6, commit=7
            print(f"[INFO] Resuming from '{resume_from}' - skipping previous phases")
        except ValueError:
            print(f"[ERROR] Invalid resume-from phase: {resume_from}")
            return 1

    # 处理 --fast-mode 参数
    if fast_mode:
        skip_po = True
        skip_qa = True
        skip_sdd = True
        print("[INFO] Fast mode enabled - skipping PO/QA/SDD validation")

    print("=" * 70)
    print("BMad Orchestrator - Epic Development Workflow")
    print("=" * 70)
    print(f"Epic ID: {epic_id}")
    print(f"Stories: {', '.join(story_ids)}")
    print(f"Base Path: {base_path}")
    print(f"Worktree Base: {worktree_base or 'Auto (parent of base_path)'}")
    print(f"Max Turns: {max_turns}")
    print(f"Mode: {mode or 'Auto-detect'}")
    print(f"UltraThink: {ultrathink}")
    print(f"Timeout: {timeout}s")
    print(f"Dry Run: {dry_run}")
    print("\nPhase Skip Settings:")
    print(f"  Skip SM: {skip_sm}")
    print(f"  Skip PO: {skip_po}")
    print(f"  Skip Analysis: {skip_analysis}")
    print(f"  Skip DEV: {skip_dev}")
    print(f"  Skip QA: {skip_qa}")
    print(f"  Skip SDD: {skip_sdd}")
    if any([skip_sm, skip_po, skip_analysis, skip_dev, skip_qa, skip_sdd]):
        entry_point = "SM"
        if skip_sm:
            entry_point = "PO"
        if skip_sm and skip_po:
            entry_point = "Analysis"
        if skip_sm and skip_po and skip_analysis:
            entry_point = "DEV"
        if skip_sm and skip_po and skip_analysis and skip_dev:
            entry_point = "QA"
        print(f"  ** Entry Point: {entry_point} **")
    print("=" * 70)

    if dry_run:
        print("\n[DRY RUN] Would execute workflow with above settings")
        print("[DRY RUN] No actual changes will be made")

        # 预览模式: 分析依赖
        from .dependency_analyzer import analyze_dependencies, print_analysis_report

        result = await analyze_dependencies(
            story_ids=story_ids,
            base_path=Path(base_path),
        )
        print("\n" + print_analysis_report(result))
        return 0

    # 确认执行 (skip if --yes flag is provided)
    if not yes:
        print("\n[WARNING] This will start an automated 24/7 development workflow.")
        print("          The workflow will run unattended until completion.")
        print("\n          Press Enter to continue, or Ctrl+C to cancel...")
        print("          (Use --yes to skip this prompt)")

        try:
            input()
        except KeyboardInterrupt:
            print("\nCancelled.")
            return 1
    else:
        print("\n[OK] Auto-confirmed with --yes flag. Starting workflow...")

    # 执行工作流
    try:
        result = await run_epic_workflow(
            epic_id=epic_id,
            story_ids=story_ids,
            base_path=base_path,
            worktree_base=worktree_base,
            max_turns=max_turns,
            mode_override=mode,
            skip_sm=skip_sm,
            skip_po=skip_po,
            skip_analysis=skip_analysis,
            skip_dev=skip_dev,
            skip_qa=skip_qa,
            skip_sdd=skip_sdd,
            timeout=timeout,
        )

        # 输出结果
        print("\n" + "=" * 70)
        print("WORKFLOW COMPLETE")
        print("=" * 70)
        print(f"Final Status: {result.get('final_status', 'unknown')}")
        print(f"Summary: {result.get('completion_summary', 'N/A')}")

        # 详细统计
        dev_outcomes = result.get("dev_outcomes", [])
        qa_outcomes = result.get("qa_outcomes", [])
        blockers = result.get("blockers", [])
        commits = result.get("commit_shas", [])

        print("\nStatistics:")
        print(f"  Stories Processed: {len(dev_outcomes)}")
        print(f"  Dev Success: {sum(1 for o in dev_outcomes if o.get('outcome') == 'SUCCESS')}")
        print(f"  QA Passed: {sum(1 for o in qa_outcomes if o.get('qa_gate') in ('PASS', 'WAIVED'))}")
        print(f"  Commits: {len(commits)}")
        print(f"  Blockers: {len(blockers)}")

        if blockers:
            print("\nBlockers:")
            for b in blockers[:5]:
                print(f"  - {b.get('story_id')}: {b.get('blocker_type')} - {b.get('description', '')[:50]}")

        return 0 if result.get("final_status") == "success" else 1

    except Exception as e:
        print(f"\n[ERROR] Workflow failed with error: {e}")
        return 1


async def cmd_epic_status(thread_id: str, checkpointer_path: str) -> int:
    """
    查看工作流状态

    Args:
        thread_id: 工作流线程 ID
        checkpointer_path: 检查点数据库路径

    Returns:
        退出码
    """
    print(f"Checking status for: {thread_id}")

    try:
        compiled = compile_graph(checkpointer_path)
        config = {"configurable": {"thread_id": thread_id}}

        state = await compiled.aget_state(config)

        if not state.values:
            print(f"\n[ERROR] No workflow found for thread: {thread_id}")
            return 1

        values = state.values
        print("\n" + "=" * 70)
        print(f"WORKFLOW STATUS: {thread_id}")
        print("=" * 70)
        print(f"Session ID: {values.get('session_id', 'N/A')}")
        print(f"Epic ID: {values.get('epic_id', 'N/A')}")
        print(f"Current Phase: {values.get('current_phase', 'N/A')}")
        print(f"Final Status: {values.get('final_status', 'in_progress')}")
        print(f"Started At: {values.get('started_at', 'N/A')}")

        # 进度详情
        story_drafts = values.get("story_drafts", [])
        approved_stories = values.get("approved_stories", [])
        dev_outcomes = values.get("dev_outcomes", [])
        qa_outcomes = values.get("qa_outcomes", [])

        print("\nProgress:")
        print(f"  SM: {len(story_drafts)} drafts created")
        print(f"  PO: {len(approved_stories)} stories approved")
        print(f"  DEV: {len(dev_outcomes)} stories developed")
        print(f"  QA: {len(qa_outcomes)} stories reviewed")

        # 阶段状态
        print("\nPhase Status:")
        print(f"  SM: {values.get('sm_status', 'pending')}")
        print(f"  PO: {values.get('po_status', 'pending')}")
        print(f"  DEV: {values.get('dev_status', 'pending')}")
        print(f"  QA: {values.get('qa_status', 'pending')}")
        print(f"  MERGE: {values.get('merge_status', 'pending')}")

        # 执行模式
        print("\nExecution:")
        print(f"  Mode: {values.get('execution_mode', 'N/A')}")
        print(f"  Current Batch: {values.get('current_batch_index', 0) + 1}/{len(values.get('parallel_batches', []))}")

        return 0

    except Exception as e:
        print(f"\n[ERROR] Failed to get status: {e}")
        return 1


async def cmd_epic_resume(thread_id: str, checkpointer_path: str) -> int:
    """
    恢复中断的工作流

    Args:
        thread_id: 工作流线程 ID
        checkpointer_path: 检查点数据库路径

    Returns:
        退出码
    """
    print(f"Resuming workflow: {thread_id}")

    try:
        result = await resume_workflow(thread_id, checkpointer_path)

        if not result:
            print(f"\n[ERROR] No workflow found to resume: {thread_id}")
            return 1

        print("\n" + "=" * 70)
        print("WORKFLOW RESUMED AND COMPLETED")
        print("=" * 70)
        print(f"Final Status: {result.get('final_status', 'unknown')}")
        print(f"Summary: {result.get('completion_summary', 'N/A')}")

        return 0 if result.get("final_status") == "success" else 1

    except Exception as e:
        print(f"\n[ERROR] Failed to resume: {e}")
        return 1


async def cmd_epic_stop(thread_id: str) -> int:
    """
    停止运行中的工作流

    Args:
        thread_id: 工作流线程 ID

    Returns:
        退出码
    """
    print(f"Stopping workflow: {thread_id}")
    # TODO: 实现停止逻辑 (需要追踪运行中的进程)
    print("[WARNING] Stop functionality is not yet implemented")
    print("          Please manually terminate Claude processes")
    return 1


# ============================================================================
# CLI 主入口
# ============================================================================

def main():
    """CLI 主入口"""
    parser = argparse.ArgumentParser(
        description="BMad Orchestrator - 全自动化 24/7 开发系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 启动 Epic 15 全自动开发
  python -m bmad_orchestrator epic-develop 15 --stories 15.1 15.2 15.3

  # 预览模式 (不执行)
  python -m bmad_orchestrator epic-develop 15 --stories 15.1 15.2 --dry-run

  # 指定并行模式
  python -m bmad_orchestrator epic-develop 15 --stories 15.1 15.2 --mode parallel

  # 查看状态
  python -m bmad_orchestrator epic-status epic-15

  # 恢复中断的工作流
  python -m bmad_orchestrator epic-resume epic-15
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="命令")

    # epic-develop 命令
    develop_parser = subparsers.add_parser(
        "epic-develop",
        help="启动 Epic 全自动化工作流"
    )
    develop_parser.add_argument("epic_id", help="Epic ID")
    develop_parser.add_argument("--stories", nargs="+", required=True, help="Story IDs")
    develop_parser.add_argument("--base-path", default=".", help="项目根目录")
    develop_parser.add_argument("--worktree-base", help="Worktree 父目录")
    develop_parser.add_argument("--max-turns", type=int, default=200, help="每个会话最大轮数")
    develop_parser.add_argument(
        "--mode",
        choices=["parallel", "linear", "hybrid"],
        help="执行模式 (默认: 自动检测)"
    )
    develop_parser.add_argument("--no-ultrathink", action="store_true", help="禁用 UltraThink")
    develop_parser.add_argument("--dry-run", action="store_true", help="预览模式")
    develop_parser.add_argument("--yes", "-y", action="store_true", help="跳过确认提示 (用于无人值守运行)")
    develop_parser.add_argument("--skip-sm", action="store_true", help="跳过SM阶段，直接从PO验证开始 (Story文件已存在时使用)")
    develop_parser.add_argument("--skip-po", action="store_true", help="跳过PO验证阶段，直接从分析开始 (Story已验证时使用)")
    develop_parser.add_argument("--skip-analysis", action="store_true", help="跳过依赖分析，使用--mode指定的模式")
    develop_parser.add_argument("--skip-dev", action="store_true", help="跳过DEV阶段，从main创建worktrees并直接运行QA (用于re-QA场景)")
    develop_parser.add_argument("--skip-qa", action="store_true", help="跳过QA审查阶段 (快速迭代模式)")
    develop_parser.add_argument("--skip-sdd", action="store_true", help="跳过SDD验证阶段")
    develop_parser.add_argument(
        "--resume-from",
        type=str,
        choices=["sm", "po", "analysis", "dev", "qa", "sdd", "merge", "commit"],
        help="从指定阶段恢复 (自动跳过之前阶段)"
    )
    develop_parser.add_argument("--timeout", type=int, default=3600, help="会话超时时间(秒)，默认3600")
    develop_parser.add_argument("--fast-mode", action="store_true", help="快速模式: 跳过PO/QA/SDD验证")

    # epic-status 命令
    status_parser = subparsers.add_parser(
        "epic-status",
        help="查看工作流状态"
    )
    status_parser.add_argument("thread_id", help="工作流线程 ID (如 epic-15)")
    status_parser.add_argument("--db", default="bmad_orchestrator.db", help="检查点数据库")

    # epic-resume 命令
    resume_parser = subparsers.add_parser(
        "epic-resume",
        help="恢复中断的工作流"
    )
    resume_parser.add_argument("thread_id", help="工作流线程 ID")
    resume_parser.add_argument("--db", default="bmad_orchestrator.db", help="检查点数据库")

    # epic-stop 命令
    stop_parser = subparsers.add_parser(
        "epic-stop",
        help="停止运行中的工作流"
    )
    stop_parser.add_argument("thread_id", help="工作流线程 ID")

    # 解析参数
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # 执行命令
    if args.command == "epic-develop":
        # Parse comma-separated story IDs (support both "16.1,16.2" and "16.1 16.2" formats)
        parsed_stories = []
        for story in args.stories:
            # Split by comma and strip whitespace
            parsed_stories.extend([s.strip() for s in story.split(",") if s.strip()])

        return asyncio.run(cmd_epic_develop(
            epic_id=args.epic_id,
            story_ids=parsed_stories,
            base_path=args.base_path,
            worktree_base=args.worktree_base,
            max_turns=args.max_turns,
            mode=args.mode,
            ultrathink=not args.no_ultrathink,
            dry_run=args.dry_run,
            yes=args.yes,
            skip_sm=args.skip_sm,
            skip_po=args.skip_po,
            skip_analysis=args.skip_analysis,
            skip_dev=args.skip_dev,
            skip_qa=args.skip_qa,
            skip_sdd=args.skip_sdd,
            resume_from=args.resume_from,
            timeout=args.timeout,
            fast_mode=args.fast_mode,
        ))
    elif args.command == "epic-status":
        return asyncio.run(cmd_epic_status(args.thread_id, args.db))
    elif args.command == "epic-resume":
        return asyncio.run(cmd_epic_resume(args.thread_id, args.db))
    elif args.command == "epic-stop":
        return asyncio.run(cmd_epic_stop(args.thread_id))

    return 1


if __name__ == "__main__":
    sys.exit(main())

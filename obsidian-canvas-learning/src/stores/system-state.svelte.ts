/**
 * Canvas Learning System - System State Store
 * Story 1.5: Sync state fields (AC-6, Task 3)
 * Story 1.8: Docker/backup management state (AC-7)
 * Story 1.9: Multi-subject management state (AC-1, AC-3)
 *
 * Manages system-level state that is not canvas-specific:
 *   - Sync engine status (Story 1.5)
 *   - Backend/Docker status
 *   - Subject management
 *   - Cross-subject settings
 */

import type { Subject } from '../types/canvas';

/** Sync engine states matching the SyncEngine state machine. */
export type SyncState = 'IDLE' | 'SYNCING' | 'OFFLINE';

class SystemState {
  // ─── Story 1.5: Sync state (AC-6, Task 3.1) ──────────────────────────
  syncState: SyncState = 'IDLE';
  pendingSyncCount = 0;
  lastSyncError: string | null = null;
  lastSuccessfulSync: Date | null = null;

  // ─── Story 1.8: Docker & Backend state ─────────────────────────────────
  backendRunning = false;
  dockerAvailable = false;
  lastBackupTime: Date | null = null;

  // ─── Story 1.9: Subject management state ───────────────────────────────
  subjects: Subject[] = [];
  activeSubjectId: string | null = null;
  crossSubjectEnabled = false;
  crossSubjectThreshold = 0.3;

  // ─── Subscriptions ─────────────────────────────────────────────────────
  private listeners: Set<() => void> = new Set();

  subscribe(fn: () => void): () => void {
    this.listeners.add(fn);
    return () => this.listeners.delete(fn);
  }

  private notify(): void {
    for (const fn of this.listeners) {
      fn();
    }
  }

  // ─── Story 1.5 methods ────────────────────────────────────────────────

  /** Update sync engine state and notify listeners. (Task 3.2) */
  setSyncState(state: SyncState): void {
    this.syncState = state;
    this.notify();
  }

  /** Update the count of pending (unsynced) Outbox entries. */
  setPendingSyncCount(count: number): void {
    this.pendingSyncCount = count;
    this.notify();
  }

  /** Record a sync error message. */
  setSyncError(error: string | null): void {
    this.lastSyncError = error;
    this.notify();
  }

  /** Record a successful sync timestamp. */
  setLastSuccessfulSync(date: Date): void {
    this.lastSuccessfulSync = date;
    this.lastSyncError = null;
    this.notify();
  }

  // ─── Story 1.8 methods ────────────────────────────────────────────────

  setBackendRunning(running: boolean): void {
    this.backendRunning = running;
    this.notify();
  }

  setDockerAvailable(available: boolean): void {
    this.dockerAvailable = available;
    this.notify();
  }

  setLastBackupTime(time: Date): void {
    this.lastBackupTime = time;
    this.notify();
  }

  // ─── Story 1.9 methods ────────────────────────────────────────────────

  loadSubjects(subjects: Subject[], activeId: string | null): void {
    this.subjects = subjects;
    this.activeSubjectId = activeId;
    this.notify();
  }

  addSubject(name: string): Subject {
    const subject: Subject = {
      id: crypto.randomUUID(),
      name,
      createdAt: new Date().toISOString(),
      isDefault: false,
    };
    this.subjects = [...this.subjects, subject];
    this.notify();
    return subject;
  }

  removeSubject(id: string): boolean {
    // Cannot delete last subject
    if (this.subjects.length <= 1) return false;
    // Cannot delete default subject
    const target = this.subjects.find(s => s.id === id);
    if (target?.isDefault) return false;

    this.subjects = this.subjects.filter(s => s.id !== id);
    // If active was deleted, reset to null
    if (this.activeSubjectId === id) {
      this.activeSubjectId = null;
    }
    this.notify();
    return true;
  }

  updateSubjectName(id: string, name: string): void {
    this.subjects = this.subjects.map(s =>
      s.id === id ? { ...s, name } : s,
    );
    this.notify();
  }

  setActiveSubject(id: string | null): void {
    this.activeSubjectId = id;
    this.notify();
  }

  setCrossSubjectEnabled(enabled: boolean): void {
    this.crossSubjectEnabled = enabled;
    this.notify();
  }

  setCrossSubjectThreshold(threshold: number): void {
    this.crossSubjectThreshold = Math.max(0, Math.min(1, threshold));
    this.notify();
  }

  /** Get the active subject name, or null for "all subjects". */
  getActiveSubjectName(): string | null {
    if (!this.activeSubjectId) return null;
    return this.subjects.find(s => s.id === this.activeSubjectId)?.name ?? null;
  }
}

/** Singleton system state instance. */
export const systemState = new SystemState();

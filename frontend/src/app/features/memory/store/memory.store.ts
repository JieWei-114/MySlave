/**
 * Memory Store
 */
import { Injectable, signal, inject } from '@angular/core';
import { MemoryApi } from '../service/memory.api';
import { Memory } from '../service/memory.model';

@Injectable({ providedIn: 'root' })
export class MemoryStore {
  // State
  memories = signal<Memory[]>([]);
  loading = signal(false);
  error = signal('');
  compressing = signal(false);

  private memoryApi = inject(MemoryApi);

  readonly currentSessionId = signal<string | null>(null);

  /**
   * Manually add a memory item
   */
  addManual(
    content: string,
    category: 'preference_or_fact' | 'important' | 'other' = 'other',
  ): void {
    const sessionId = this.currentSessionId();
    if (!sessionId) return;

    this.memoryApi.addMemory(content, sessionId, category).subscribe({
      next: (m) => {
        this.memories.update((list) => [...list, m as Memory]);
      },
      error: () => {
        this.error.set('Failed to save memory');
      },
    });
  }

  /**
   * Load all memories for a session
   */
  load(sessionId: string) {
    this.currentSessionId.set(sessionId);
    this.loading.set(true);

    this.memoryApi.getMemories(sessionId).subscribe((m) => {
      this.memories.set(m);
      this.loading.set(false);
    });
  }

  /**
   * Toggle memory enabled/disabled state
   */
  toggle(m: Memory) {
    const action = m.enabled ? this.memoryApi.disable(m.id) : this.memoryApi.enable(m.id);

    action.subscribe(() => {
      this.memories.update((list) =>
        list.map((x) => (x.id === m.id ? { ...x, enabled: !x.enabled } : x)),
      );
    });
  }

  /**
   * Delete a memory item
   */
  delete(m: Memory) {
    this.memoryApi.delete(m.id).subscribe(() => {
      this.memories.update((list) => list.filter((x) => x.id !== m.id));
    });
  }

  /**
   * Search memories by query string
   */
  search(q: string) {
    const sessionId = this.currentSessionId();
    if (!sessionId) return;

    this.memoryApi.search(sessionId, q).subscribe((res) => {
      this.memories.set(res);
    });
  }

  /**
   * Compress and synthesize memories using AI
   * Reduces memory count while preserving important information
   */
  compress(model: string) {
    const sessionId = this.currentSessionId();
    if (!sessionId || this.compressing()) return;

    this.compressing.set(true);

    this.memoryApi.compress(sessionId, model).subscribe({
      next: (m: any) => {
        if (m?.id) {
          this.memories.update((list) => [...list, m]);
        }
      },
      complete: () => {
        this.compressing.set(false);
        this.load(sessionId);
      },
      error: () => this.compressing.set(false),
    });
  }

  /**
   * Reload memories for current session
   */
  reload(sessionId: string) {
    this.loading.set(true);

    this.memoryApi.getMemories(sessionId).subscribe({
      next: (m) => {
        this.memories.set(m);
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
      },
    });
  }
}

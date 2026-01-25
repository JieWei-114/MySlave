import { Injectable, signal, inject } from '@angular/core';
import { MemoryApi } from '../service/memory.api';
import { Memory } from '../service/memory.model';

@Injectable({ providedIn: 'root' })
export class MemoryStore {
  memories = signal<Memory[]>([]);
  loading = signal(false);
  error = signal('');
  compressing = signal(false);

  private memoryApi = inject(MemoryApi);
  private sessionId: string | null = null;

  readonly currentSessionId = signal<string | null>(null);

  addManual(content: string): void {
    const sessionId = this.currentSessionId();
    if (!sessionId) return;

    this.memoryApi.addMemory(content, sessionId).subscribe({
      next: (m) => {
        this.memories.update((list) => [...list, m as Memory]);
      },
      error: () => {
        this.error.set('Failed to save memory');
      },
    });
  }

  load(sessionId: string) {
    this.currentSessionId.set(sessionId);
    this.loading.set(true);

    this.memoryApi.getMemories(sessionId).subscribe((m) => {
      this.memories.set(m);
      this.loading.set(false);
    });
  }

  toggle(m: Memory) {
    const action = m.enabled ? this.memoryApi.disable(m.id) : this.memoryApi.enable(m.id);

    action.subscribe(() => {
      this.memories.update((list) =>
        list.map((x) => (x.id === m.id ? { ...x, enabled: !x.enabled } : x)),
      );
    });
  }

  delete(m: Memory) {
    this.memoryApi.delete(m.id).subscribe(() => {
      this.memories.update((list) => list.filter((x) => x.id !== m.id));
    });
  }

  search(q: string) {
    const sessionId = this.currentSessionId();
    if (!sessionId) return;

    this.memoryApi.search(sessionId, q).subscribe((res) => {
      this.memories.set(res);
    });
  }

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
      complete: () => this.compressing.set(false),
      error: () => this.compressing.set(false),
    });
  }

  setSession(sessionId: string) {
    this.sessionId = sessionId;
    this.reload(sessionId);
  }

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

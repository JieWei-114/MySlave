import { Injectable, signal, inject } from '@angular/core';
import { MemoryApi } from '../service/memory.api';
import { Memory } from '../service/memory.model';
import { ChatMessage } from '../../chat/services/chat.model';
import { ChatStore } from '../../chat/store/chat.store';

@Injectable({ providedIn: 'root' })
export class MemoryStore {
  memories = signal<Memory[]>([]);
  loading = signal(false);
  error = signal('');

  private memoryApi = inject(MemoryApi);
  private chatStore = inject(ChatStore);

  readonly currentSessionId = signal<string | null>(null);

  private saveMemory(content: string): void {
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

  rememberMessage(message: ChatMessage): void {
    if (message.remembered) return;
    this.saveMemory(message.content);
    message.remembered = true;
  }

  addManual(content: string): void {
    this.saveMemory(content);
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

  compress() {
    const sessionId = this.currentSessionId();
    if (!sessionId) return;

    const model = this.chatStore.currentModel().id;

    this.memoryApi.compress(sessionId, model).subscribe((m: any) => {
      if (m?.id) {
        this.memories.update((list) => [...list, m]);
      }
    });
  }
}

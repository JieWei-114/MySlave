import { Injectable, signal, computed, inject, effect } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { PLATFORM_ID } from '@angular/core';

import { ChatApi } from '../services/chat.api';
import {
  ChatMessage,
  ChatSession,
  AVAILABLE_MODELS,
  DEFAULT_MODEL,
  AIModel,
} from '../services/chat.model';
import { MemoryStore } from '../../memory/store/memory.store';

@Injectable({ providedIn: 'root' })
export class ChatStore {
  private chatApi = inject(ChatApi);
  private platformId = inject(PLATFORM_ID);
  private memoryStore = inject(MemoryStore);

  private isBrowser = isPlatformBrowser(this.platformId);

  /** ============================
   *  State
   *  ============================ */

  private sessions = signal<Record<string, ChatSession>>({});
  readonly currentSessionId = signal<string | null>(null);

  readonly loading = signal(false);
  readonly error = signal('');

  readonly currentModel = signal<AIModel>(DEFAULT_MODEL);
  readonly availableModels = signal<AIModel[]>(AVAILABLE_MODELS);
  readonly draftMessage = signal('');

  /** ============================
   *  Derived
   *  ============================ */

  readonly sessionList = computed(() => Object.values(this.sessions()));

  readonly sessionIds = computed(() => Object.keys(this.sessions()));

  readonly currentSession = computed(() => {
    const id = this.currentSessionId();
    return id ? (this.sessions()[id] ?? null) : null;
  });

  readonly messageList = computed<ChatMessage[]>(() => this.currentSession()?.messages ?? []);

  readonly hasMessages = computed(() => this.messageList().length > 0);

  readonly isEmpty = computed(() => !this.hasMessages() && !this.loading());

  readonly canSendMessage = computed(() => !this.loading() && this.currentSessionId() !== null);

    /** ============================
   *  Sidebar
   *  ============================ */

  readonly visibleSessions = computed(() => {
    const active = this.currentSessionId();

    return Object.values(this.sessions()).filter(
      (s) => s.id === active || s.messages.length > 0 || s.title !== 'New chat',
    );
  });

  /** ============================
   *  Draft handling
   *  ============================ */

  setDraftMessage(message: string): void {
    this.draftMessage.set(message);
  }

  appendToDraft(message: string): void {
    const current = this.draftMessage();
    const separator = current.trim().length ? '\n' : '';
    this.draftMessage.set(`${current}${separator}${message}`);
  }

  clearDraft(): void {
    this.draftMessage.set('');
  }

  /** ============================
   *  Model Selection
   *  ============================ */

  setModel(model: AIModel): void {
    this.currentModel.set(model);
  }

  /** ============================
   *  Init
   *  ============================ */

  loadSessions(): void {
    this.loading.set(true);
    this.error.set('');

    this.chatApi.getSessions().subscribe({
      next: (sessions) => {
        if (!sessions || sessions.length === 0) {
          this.sessions.set({});
          this.loading.set(false);

          this.createTempSession();
          return;
        }

        const map: Record<string, ChatSession> = {};

        for (const s of sessions) {
          map[s.id] = {
            id: s.id,
            title: s.title,
            messages: [],
          };
        }

        this.sessions.set(map);
        this.currentSessionId.set(sessions[0].id);

        this.loading.set(false);
      },
      error: () => {
        this.error.set('Failed to load sessions');
        this.loading.set(false);
      },
    });
  }

  /** ============================
   *  Session
   *  ============================ */

  selectSession(id: string): void {
    this.currentSessionId.set(id);
    this.error.set('');

    const session = this.sessions()[id];

    if (!session) {
      this.sessions.update((s) => ({
        ...s,
        [id]: {
          id,
          title: 'New chat',
          messages: [],
        },
      }));
      return;
    }

    if (session.messages.length > 0) return;

    if (session.title === 'New chat') return;

    this.chatApi.getSessionbyId(id).subscribe({
      next: (fullSession) => {
        this.sessions.update((s) => ({
          ...s,
          [id]: fullSession,
        }));
      },
      error: () => {
        console.warn('Session not found in backend:', id);
      },
    });
  }

  createTempSession(): void {
    const id = crypto.randomUUID();

    this.sessions.update((s) => ({
      ...s,
      [id]: {
        id,
        title: 'New chat',
        messages: [],
      },
    }));

    this.currentSessionId.set(id);
  }

  deleteSession(sessionId: string): void {
    const wasActive = this.currentSessionId() === sessionId;

    this.chatApi.deleteSession(sessionId).subscribe({
      next: () => {
        this.sessions.update((s) => {
          const copy = { ...s };
          delete copy[sessionId];
          return copy;
        });

        if (wasActive) {
          const next = this.sessionIds()[0] ?? null;
          this.currentSessionId.set(next);
        }
      },
      error: () => {
        this.error.set('Failed to delete session');
      },
    });
  }

  renameSession(id: string, title: string): void {
    this.sessions.update((s) => ({
      ...s,
      [id]: {
        ...s[id],
        title,
      },
    }));

    this.chatApi.renameSession(id, title).subscribe({
      error: () => {
        this.error.set('Failed to rename session');
      },
    });
  }

  /** ============================
   *  Messages
   *  ============================ */

  private createMessage(role: 'user' | 'assistant', content: string): ChatMessage {
    return {
      role,
      content,
      created_at: new Date().toISOString(),
    };
  }

  stopStreaming: (() => void) | null = null;

  sendMessage(content: string): void {
    if (!content.trim()) return;

    const tempId = this.currentSessionId();
    if (!tempId) return;

    const tempSession = this.sessions()[tempId];

    const isTempSession =
      !tempSession || (tempSession.title === 'New chat' && tempSession.messages.length === 0);

    const generatedTitle = content.split('\n')[0].slice(0, 40);

    this.loading.set(true);
    this.error.set('');

    const startStreaming = (sessionId: string) => {
      const session = this.sessions()[sessionId] ?? {
        id: sessionId,
        title: generatedTitle,
        messages: [],
      };

      this.sessions.update((s) => ({
        ...s,
        [sessionId]: {
          ...session,
          messages: [...session.messages, this.createMessage('user', content)],
        },
      }));

      let assistantIndex = -1;
      this.sessions.update((s) => {
        assistantIndex = s[sessionId].messages.length;
        return {
          ...s,
          [sessionId]: {
            ...s[sessionId],
            messages: [...s[sessionId].messages, this.createMessage('assistant', '')],
          },
        };
      });

      /** real SSE streaming */
      this.stopStreaming = this.chatApi.streamMessage(
        sessionId,
        content,
        this.currentModel().id,
        (token) => {
          this.sessions.update((s) => {
            const msgs = [...s[sessionId].messages];
            msgs[assistantIndex] = {
              ...msgs[assistantIndex],
              content: msgs[assistantIndex].content + token,
            };
            return { ...s, [sessionId]: { ...s[sessionId], messages: msgs } };
          });
        },
        () => {
          this.loading.set(false);
          this.stopStreaming = null;

          this.memoryStore.reload(sessionId);
        },
      );
    };

    if (isTempSession) {
      this.chatApi.createSession(generatedTitle).subscribe({
        next: (session) => {
          this.sessions.update((s) => {
            const copy = { ...s };
            delete copy[tempId];
            return {
              ...copy,
              [session.id]: {
                id: session.id,
                title: session.title,
                messages: [],
              },
            };
          });

          this.currentSessionId.set(session.id);
          startStreaming(session.id);
        },
        error: () => {
          this.error.set('Failed to create session');
          this.loading.set(false);
        },
      });
    } else {
      startStreaming(tempId);
    }
  }

  stop(): void {
    this.stopStreaming?.();
    this.stopStreaming = null;
    this.loading.set(false);
  }

  /** ============================
   *  state
   *  ============================ */

  loadLatestMessages(sessionId: string): void {
    const session = this.sessions()[sessionId];
    if (!session) return;

    if (session.messages.length) return;

    this.sessions.update((s) => ({
      ...s,
      [sessionId]: {
        ...s[sessionId],
        loadingMore: true,
      },
    }));

    this.chatApi.getMessages(sessionId, 20).subscribe({
      next: (msgs) => {
        this.sessions.update((s) => ({
          ...s,
          [sessionId]: {
            ...s[sessionId],
            messages: msgs,
            hasMore: msgs.length === 20,
            loadingMore: false,
          },
        }));
      },
      error: () => {
        this.sessions.update((s) => ({
          ...s,
          [sessionId]: {
            ...s[sessionId],
            loadingMore: false,
          },
        }));
      },
    });
  }

  loadOlderMessages(sessionId: string): void {
    const session = this.sessions()[sessionId];
    if (!session) return;

    if (session.loadingMore || session.hasMore === false) return;
    if (!session.messages.length) return;

    const before = new Date(session.messages[0].created_at).toISOString();

    this.sessions.update((s) => ({
      ...s,
      [sessionId]: {
        ...s[sessionId],
        loadingMore: true,
      },
    }));

    this.chatApi.getMessages(sessionId, 20, before).subscribe({
      next: (older) => {
        this.sessions.update((s) => ({
          ...s,
          [sessionId]: {
            ...s[sessionId],
            messages: [...older, ...s[sessionId].messages],
            hasMore: older.length === 20,
            loadingMore: false,
          },
        }));
      },
      error: () => {
        this.sessions.update((s) => ({
          ...s,
          [sessionId]: {
            ...s[sessionId],
            loadingMore: false,
          },
        }));
      },
    });
  }

  
  /** ============================
   *  Helpers
   *  ============================ */

  private pushUserMessage(id: string, content: string) {
    this.sessions.update((s) => ({
      ...s,
      [id]: {
        ...s[id],
        messages: [...s[id].messages, this.createMessage('user', content)],
      },
    }));
  }

  private pushAssistantMessage(id: string, content: string) {
    this.sessions.update((s) => ({
      ...s,
      [id]: {
        ...s[id],
        messages: [...s[id].messages, this.createMessage('assistant', content)],
      },
    }));
  }
}
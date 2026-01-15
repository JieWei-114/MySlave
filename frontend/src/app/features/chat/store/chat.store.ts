import {
  Injectable,
  signal,
  computed,
  effect,
  inject
} from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { PLATFORM_ID } from '@angular/core';

import { ChatApi } from '../services/chat.api';
import { ChatMessage } from '../services/chat.model';
import { ChatSession } from '../services/chat-session.model';

@Injectable({ providedIn: 'root' })
export class ChatStore {
  private chatApi = inject(ChatApi);
  private platformId = inject(PLATFORM_ID);
  private isBrowser = isPlatformBrowser(this.platformId);

  /** ============================
   *  State
   *  ============================ */

  private sessions = signal<Record<string, ChatSession>>({});
  readonly currentSessionId = signal<string | null>(null);

  readonly loading = signal(false);
  readonly error = signal('');

  /** ============================
   *  Derived
   *  ============================ */

  readonly sessionList = computed(() =>
    Object.values(this.sessions())
  );

  readonly sessionIds = computed(() =>
    Object.keys(this.sessions())
  );

  readonly currentSession = computed(() => {
    const id = this.currentSessionId();
    return id ? this.sessions()[id] ?? null : null;
  });

  readonly messageList = computed<ChatMessage[]>(() =>
    this.currentSession()?.messages ?? []
  );

  /** Sidebar 显示规则 */
  readonly visibleSessions = computed(() => {
    const active = this.currentSessionId();

    return Object.values(this.sessions()).filter(s =>
      s.id === active ||
      s.messages.length > 0 ||
      s.title !== 'New chat'
    );
  });

  /** ============================
   *  Init
   *  ============================ */

  loadSessions(): void {
    this.loading.set(true);
    this.error.set('');

    this.chatApi.getSessions().subscribe({
      next: sessions => {
        if (!sessions || sessions.length === 0) {
          // ✅ DB 没数据是正常状态
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
            messages: []
          };
        }

        this.sessions.set(map);
        this.currentSessionId.set(sessions[0].id);

        this.loading.set(false);
      },
      error: () => {
        // ❌ 只有真的请求失败才报错
        this.error.set('Failed to load sessions');
        this.loading.set(false);
      }
    });
  }

  /** ============================
   *  Session
   *  ============================ */

  selectSession(id: string): void {
    this.currentSessionId.set(id);
    this.error.set('');

    const session = this.sessions()[id];

    // ✅ 本地不存在 → 一定是 temp（New chat）
    if (!session) {
      this.sessions.update(s => ({
        ...s,
        [id]: {
          id,
          title: 'New chat',
          messages: []
        }
      }));
      return;
    }

    // ✅ 已经有 messages，不再拉
    if (session.messages.length > 0) return;

    // ✅ New chat / temp session 不打 backend
    if (session.title === 'New chat') return;

    // ✅ 只有「真实 session + 没拉过 message」才请求
    this.chatApi.getSessionbyId(id).subscribe({
      next: fullSession => {
        this.sessions.update(s => ({
          ...s,
          [id]: fullSession
        }));
      },
      error: () => {
        // ❌ 不要报错（可能是刚创建、或被删）
        console.warn('Session not found in backend:', id);
      }
    });
  }

  // createSessionFromBackend(): void {
  //   this.loading.set(true);

  //   this.chatApi.createSession('New chat').subscribe({
  //     next: session => {
  //       this.sessions.update(s => ({
  //         ...s,
  //         [session.id]: session
  //       }));
  //       this.currentSessionId.set(session.id);
  //       this.loading.set(false);
  //     },
  //     error: () => {
  //       this.error.set('Failed to create session');
  //       this.loading.set(false);
  //     }
  //   });
  // }

  createTempSession(): void {
    const id = crypto.randomUUID();

    this.sessions.update(s => ({
      ...s,
      [id]: {
        id,
        title: 'New chat',
        messages: []
      }
    }));

    this.currentSessionId.set(id);
  }

  deleteSession(sessionId: string): void {
    const wasActive = this.currentSessionId() === sessionId;

    this.chatApi.deleteSession(sessionId).subscribe({
      next: () => {
        this.sessions.update(s => {
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
      }
    });
  }

  // clearSession(id: string): void {
  //   this.sessions.update(s => {
  //     const copy = { ...s };
  //     delete copy[id];
  //     return copy;
  //   });

  //   if (this.currentSessionId() === id) {
  //     const next = this.sessionIds()[0] ?? null;
  //     this.currentSessionId.set(next);
  //   }
  // }

  renameSession(id: string, title: string): void {
    // ✅ 先本地更新（秒响应）
    this.sessions.update(s => ({
      ...s,
      [id]: {
        ...s[id],
        title
      }
    }));

    // ✅ 同步 backend
    this.chatApi.renameSession(id, title).subscribe({
      error: () => {
        this.error.set('Failed to rename session');
      }
    });
  }
  /** ============================
   *  Messages
   *  ============================ */

  private createMessage(
    role: 'user' | 'assistant',
    content: string
  ): ChatMessage {
    return {
      role,
      content,
      created_at: new Date().toISOString()
    };
  }

  stopStreaming: (() => void) | null = null;

  sendMessage(content: string): void {
    if (!content.trim()) return;

    const tempId = this.currentSessionId();
    if (!tempId) return;

    const tempSession = this.sessions()[tempId];

    const isTempSession =
      !tempSession ||
      (tempSession.title === 'New chat' &&
      tempSession.messages.length === 0);

    const generatedTitle = content.split('\n')[0].slice(0, 40);

    this.loading.set(true);
    this.error.set('');

    const startStreaming = (sessionId: string) => {
      const session =
        this.sessions()[sessionId] ?? {
          id: sessionId,
          title: generatedTitle,
          messages: []
        };

      /** 1️⃣ push user message */
      this.sessions.update(s => ({
        ...s,
        [sessionId]: {
          ...session,
          messages: [...session.messages, this.createMessage( 'user', content )]
        }
      }));

      /** 2️⃣ 占位 assistant */
      let assistantIndex = -1;
      this.sessions.update(s => {
        assistantIndex = s[sessionId].messages.length;
        return {
          ...s,
          [sessionId]: {
            ...s[sessionId],
            messages: [
              ...s[sessionId].messages,
              this.createMessage('assistant', '') 
            ]
          }
        };
      });

      /** 3️⃣ 真 SSE streaming */
      this.stopStreaming = this.chatApi.streamMessage(
        sessionId,
        content,
        token => {
          this.sessions.update(s => {
            const msgs = [...s[sessionId].messages];
            msgs[assistantIndex] = {
              ...msgs[assistantIndex],
              content: this.appendToken(msgs[assistantIndex].content, token)
            };
            return { ...s, [sessionId]: { ...s[sessionId], messages: msgs } };
          });
        },
        () => {
          this.loading.set(false);
          this.stopStreaming = null;
        }
      );
    };

    /** 第一次消息：创建真实 session */
    if (isTempSession) {
      this.chatApi.createSession(generatedTitle).subscribe({
        next: session => {
          this.sessions.update(s => {
            const copy = { ...s };
            delete copy[tempId];
            return {
              ...copy,
              [session.id]: {
                id: session.id,
                title: session.title,
                messages: []
              }
            };
          });

          this.currentSessionId.set(session.id);
          startStreaming(session.id);
        },
        error: () => {
          this.error.set('Failed to create session');
          this.loading.set(false);
        }
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

  private appendToken(prev: string, token: string): string {
    if (!prev) return token;

    const needSpace =
      /[a-zA-Z0-9]$/.test(prev) &&
      /^[a-zA-Z0-9]/.test(token);

    return needSpace ? prev + ' ' + token : prev + token;
  }

  /** ============================
   *  Helpers
   *  ============================ */

  private pushUserMessage(id: string, content: string) {
    this.sessions.update(s => ({
      ...s,
      [id]: {
        ...s[id],
        messages: [...s[id].messages, this.createMessage('user', content)]
      }
    }));
  }

  private pushAssistantMessage(id: string, content: string) {
    this.sessions.update(s => ({
      ...s,
      [id]: {
        ...s[id],
        messages: [...s[id].messages, this.createMessage('assistant', content)]
      }
    }));
  }

    /** ============================
   *  state
   *  ============================ */

 loadLatestMessages(sessionId: string): void {
    const session = this.sessions()[sessionId];
    if (!session) return;

    // 已经加载过就不重复拉
    if (session.messages.length) return;

    this.sessions.update(s => ({
      ...s,
      [sessionId]: {
        ...s[sessionId],
        loadingMore: true
      }
    }));

    this.chatApi.getMessages(sessionId, 20).subscribe({
      next: msgs => {
        this.sessions.update(s => ({
          ...s,
          [sessionId]: {
            ...s[sessionId],
            messages: msgs,
            hasMore: msgs.length === 20,
            loadingMore: false
          }
        }));
      },
      error: () => {
        this.sessions.update(s => ({
          ...s,
          [sessionId]: {
            ...s[sessionId],
            loadingMore: false
          }
        }));
      }
    });
  }

  
  loadOlderMessages(sessionId: string): void {
    const session = this.sessions()[sessionId];
    if (!session) return;

    if (session.loadingMore || session.hasMore === false) return;
    if (!session.messages.length) return;

    const before = new Date(
      session.messages[0].created_at
    ).toISOString();

    this.sessions.update(s => ({
      ...s,
      [sessionId]: {
        ...s[sessionId],
        loadingMore: true
      }
    }));

    this.chatApi.getMessages(sessionId, 20, before).subscribe({
      next: older => {
        this.sessions.update(s => ({
          ...s,
          [sessionId]: {
            ...s[sessionId],
            messages: [...older, ...s[sessionId].messages],
            hasMore: older.length === 20,
            loadingMore: false
          }
        }));
      },
      error: () => {
        this.sessions.update(s => ({
          ...s,
          [sessionId]: {
            ...s[sessionId],
            loadingMore: false
          }
        }));
      }
    });
  }
}

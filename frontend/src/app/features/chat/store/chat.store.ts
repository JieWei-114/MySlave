/**
 * Chat Store
 * Central state management for chat sessions and messages
 */
import { Injectable, signal, computed, inject } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { PLATFORM_ID } from '@angular/core';

import { ChatApi } from '../services/chat.api';
import {
  ChatMessage,
  ChatSession,
  AVAILABLE_MODELS,
  DEFAULT_MODEL,
  AIModel,
  MessageMetadata,
} from '../services/chat.model';
import { MemoryStore } from '../../memory/store/memory.store';
import { MemoryApi } from '../../memory/service/memory.api';
import { RulesApiService } from '../../rules/service/rules.api';
import { DEFAULT_RULES, type RulesConfig } from '../../rules/service/rules.model';

@Injectable({ providedIn: 'root' })
export class ChatStore {
  private chatApi = inject(ChatApi);
  private memoryApi = inject(MemoryApi);
  private rulesApi = inject(RulesApiService);
  private platformId = inject(PLATFORM_ID);
  private memoryStore = inject(MemoryStore);

  private isBrowser = isPlatformBrowser(this.platformId);
  private log(...args: unknown[]): void {
    console.debug(...args);
  }

  private logError(...args: unknown[]): void {
    console.error(...args);
  }

  /**
   * State Signals
   */

  // All chat sessions stored as a dictionary for efficient lookups
  private sessions = signal<Record<string, ChatSession>>({});

  // ID of the currently active session
  readonly currentSessionId = signal<string | null>(null);

  // Loading state for async operations
  readonly loading = signal(false);

  // Error messages to display to the user
  readonly error = signal('');

  // Currently selected AI model for chat
  readonly currentModel = signal<AIModel>(DEFAULT_MODEL);
  readonly availableModels = signal<AIModel[]>(AVAILABLE_MODELS);

  // Draft message being typed by the user
  readonly draftMessage = signal('');
  private readonly draftBySession = signal<Record<string, string>>({});

  // Metadata from last AI response
  readonly lastMessageMetadata = signal<MessageMetadata | null>(null);

  // Verification status during streaming
  readonly verificationStatus = signal<{
    type: 'idle' | 'verifying' | 'verified';
    message?: string;
    data?: any;
  }>({ type: 'idle' });

  // Feature availability flags
  readonly hasMemory = signal<boolean>(false);
  readonly hasFile = signal<boolean>(false);

  /**
   * Computed Signals
   */

  // Convert sessions dictionary to array for iteration
  readonly sessionList = computed(() => Object.values(this.sessions()));
  readonly sessionIds = computed(() => Object.keys(this.sessions()));

  // Get the currently active session
  readonly currentSession = computed(() => {
    const id = this.currentSessionId();
    return id ? (this.sessions()[id] ?? null) : null;
  });

  // Get follow-up status from current session's rules (default: false)
  readonly followUpEnabled = computed(() => {
    const session = this.currentSession();
    return session?.rules?.followUpEnabled ?? false;
  });

  // Get reasoning status from current session's rules (default: false)
  readonly reasoningEnabled = computed(() => {
    const session = this.currentSession();
    return session?.rules?.reasoningEnabled ?? false;
  });

  // Messages in the current session
  readonly messageList = computed<ChatMessage[]>(() => this.currentSession()?.messages ?? []);
  readonly hasMessages = computed(() => this.messageList().length > 0);

  // Empty state check for showing welcome screen
  readonly isEmpty = computed(() => !this.hasMessages() && !this.loading());

  // Can only send if not loading and session exists
  readonly canSendMessage = computed(() => !this.loading() && this.currentSessionId() !== null);

  /**
   * Sidebar Helper
   */

  // Only show sessions that are active, have messages, or have custom titles
  // Hides empty "New chat" sessions from sidebar
  readonly visibleSessions = computed(() => {
    const active = this.currentSessionId();

    return (Object.values(this.sessions()) as ChatSession[]).filter(
      (s: ChatSession) => s.id === active || s.messages.length > 0 || s.title !== 'New chat',
    );
  });

  /**
   * Draft Message Handling
   */

  // Update the draft message
  setDraftMessage(message: string): void {
    this.draftMessage.set(message);
    const sessionId = this.currentSessionId();
    if (!sessionId) return;
    this.draftBySession.update((drafts: Record<string, string>) => ({
      ...drafts,
      [sessionId]: message,
    }));
  }

  /**
   * Append text to draft (useful for inserting memory context)
   */
  appendToDraft(message: string): void {
    const current = this.draftMessage();
    const separator = current.trim().length ? '\n' : '';
    this.setDraftMessage(`${current}${separator}${message}`);
  }

  /**
   * Clear draft after sending message
   */
  clearDraft(): void {
    this.setDraftMessage('');
  }

  /**
   * Model Selection
   */

  // Set the active AI model (e.g., Gemma, Qwen)
  setModel(model: AIModel): void {
    this.currentModel.set(model);
    // Save model choice to localStorage for this session
    const sessionId = this.currentSessionId();
    if (sessionId) {
      this.saveModelToLocalStorage(sessionId, model);
    }
  }

  /**
   * Save model selection to localStorage with session-specific key
   */
  private saveModelToLocalStorage(sessionId: string, model: AIModel): void {
    if (!this.isBrowser) return;
    try {
      localStorage.setItem(`chat_model_${sessionId}`, JSON.stringify(model));
      this.log(`Model saved to localStorage for session ${sessionId}`);
    } catch (e) {
      this.logError(`Failed to save model to localStorage: ${e}`);
    }
  }

  /**
   * Load model selection from localStorage for a specific session
   */
  private loadModelFromLocalStorage(sessionId: string): AIModel | null {
    if (!this.isBrowser) return null;
    try {
      const stored = localStorage.getItem(`chat_model_${sessionId}`);
      if (stored) {
        const model = JSON.parse(stored) as AIModel;
        this.log(`Model loaded from localStorage for session ${sessionId}`);
        return model;
      }
    } catch (e) {
      this.logError(`Failed to load model from localStorage: ${e}`);
    }
    return null;
  }

  /**
   * Follow-up & Metadata
   */

  /**
   * Toggle follow-up context usage for current session
   * Updates session-specific rules in backend
   */
  toggleFollowUp(): void {
    const session = this.currentSession();
    if (!session) return;

    const currentValue = session.rules?.followUpEnabled ?? false;
    const newValue = !currentValue;

    // Optimistically update local state
    this.sessions.update((sessions: Record<string, ChatSession>) => ({
      ...sessions,
      [session.id]: {
        ...session,
        rules: {
          ...DEFAULT_RULES,
          ...session.rules,
          followUpEnabled: newValue,
        },
      },
    }));

    // Persist to backend
    const updatedRules: RulesConfig = {
      ...DEFAULT_RULES,
      ...session.rules,
      followUpEnabled: newValue,
    };

    this.rulesApi.updateSessionRules(session.id, updatedRules).subscribe({
      next: (rules: RulesConfig) => {
        this.log(`Follow-up toggled to ${newValue} for session ${session.id}`);
        // Update with response from server to ensure consistency
        this.sessions.update((sessions: Record<string, ChatSession>) => ({
          ...sessions,
          [session.id]: {
            ...session,
            rules: rules,
          },
        }));
      },
      error: (err: any) => {
        this.logError(`Failed to update follow-up setting: ${err}`);
        // Revert optimistic update on error
        this.sessions.update((sessions: Record<string, ChatSession>) => ({
          ...sessions,
          [session.id]: {
            ...session,
            rules: {
              ...DEFAULT_RULES,
              ...session.rules,
              followUpEnabled: currentValue,
            },
          },
        }));
        this.error.set('Failed to update follow-up setting');
      },
    });
  }

  /**
   * Toggle reasoning generation for the current session.
   * Updates session-specific rules in backend
   */
  toggleReasoning(): void {
    const session = this.currentSession();
    if (!session) return;

    const currentValue = session.rules?.reasoningEnabled ?? false;
    const newValue = !currentValue;

    // Optimistically update local state
    this.sessions.update((sessions: Record<string, ChatSession>) => ({
      ...sessions,
      [session.id]: {
        ...session,
        rules: {
          ...DEFAULT_RULES,
          ...session.rules,
          reasoningEnabled: newValue,
        },
      },
    }));

    // Persist to backend
    const updatedRules: RulesConfig = {
      ...DEFAULT_RULES,
      ...session.rules,
      reasoningEnabled: newValue,
    };

    this.rulesApi.updateSessionRules(session.id, updatedRules).subscribe({
      next: (rules: RulesConfig) => {
        this.log(`Reasoning toggled to ${newValue} for session ${session.id}`);
        // Update with response from server to ensure consistency
        this.sessions.update((sessions: Record<string, ChatSession>) => ({
          ...sessions,
          [session.id]: {
            ...session,
            rules: rules,
          },
        }));
      },
      error: (err: any) => {
        this.logError(`Failed to update reasoning setting: ${err}`);
        // Revert optimistic update on error
        this.sessions.update((sessions: Record<string, ChatSession>) => ({
          ...sessions,
          [session.id]: {
            ...session,
            rules: {
              ...DEFAULT_RULES,
              ...session.rules,
              reasoningEnabled: currentValue,
            },
          },
        }));
        this.error.set('Failed to update reasoning setting');
      },
    });
  }

  /**
   * Store metadata from the last AI response
   */
  setLastMessageMetadata(metadata: MessageMetadata): void {
    this.lastMessageMetadata.set(metadata);
  }

  /**
   * Check if the session has stored memories
   * Updates hasMemory flag to enable/disable memory source
   */
  checkMemoryAvailability(sessionId: string): void {
    this.memoryApi.getMemories(sessionId).subscribe({
      next: (memories: any[]) => {
        this.hasMemory.set(memories.length > 0);
      },
      error: () => this.hasMemory.set(false),
    });
  }

  /**
   * Load all chat sessions from backend
   */
  loadSessions(): void {
    this.log('Loading chat sessions');
    this.loading.set(true);
    this.error.set('');

    this.chatApi.getSessions().subscribe({
      next: (sessions: any[]) => {
        if (!sessions || sessions.length === 0) {
          this.log('No sessions found, creating temp session');
          this.sessions.set({});
          this.loading.set(false);

          this.createTempSession();
          return;
        }

        // Convert array to dictionary for efficient lookups
        const map: Record<string, ChatSession> = {};

        for (const s of sessions) {
          map[s.id] = {
            id: s.id,
            title: s.title,
            messages: [], // Messages loaded lazily when session is selected
          };
        }

        this.sessions.set(map);
        this.currentSessionId.set(sessions[0].id);
        this.log(`Sessions loaded: ${sessions.length}`);

        this.loading.set(false);
      },
      error: (err: unknown) => {
        this.logError(`Failed to load sessions: ${err}`);
        this.error.set('Failed to load sessions');
        this.loading.set(false);
      },
    });
  }

  /**
   * Session Management
   * CRUD operations for chat sessions
   */

  /**
   * Select and activate a chat session
   */
  selectSession(id: string): void {
    this.log(`Selecting session: ${id}`);
    const previousId = this.currentSessionId();
    if (previousId && previousId !== id) {
      const currentDraft = this.draftMessage();
      this.draftBySession.update((drafts: Record<string, string>) => ({
        ...drafts,
        [previousId]: currentDraft,
      }));
    }

    this.currentSessionId.set(id);
    this.error.set('');

    const nextDraft = this.draftBySession()[id] ?? '';
    this.draftMessage.set(nextDraft);

    // Load model for this session from localStorage
    const savedModel = this.loadModelFromLocalStorage(id);
    if (savedModel) {
      this.currentModel.set(savedModel);
    } else {
      // Fall back to default model if none saved
      this.currentModel.set(DEFAULT_MODEL);
    }

    const session = this.sessions()[id];

    // Create session if it doesn't exist (happens with URL navigation)
    if (!session) {
      this.sessions.update((s: Record<string, ChatSession>) => ({
        ...s,
        [id]: {
          id,
          title: 'New chat',
          messages: [],
        },
      }));
      return;
    }

    // Skip loading if messages already cached
    if (session.messages.length > 0) return;

    // Don't load messages for unsaved temp sessions
    if (session.title === 'New chat') return;

    // Load full session data from backend
    this.chatApi.getSessionbyId(id).subscribe({
      next: (fullSession: ChatSession) => {
        this.log(`Session loaded from server: ${id}`);
        this.sessions.update((s: Record<string, ChatSession>) => ({
          ...s,
          [id]: fullSession,
        }));
      },
      error: (err: unknown) => {
        this.logError(`Failed to load session ${id}: ${err}`);
      },
    });
  }

  /**
   * Create a temporary session (not saved to backend yet)
   * Will be persisted when first message is sent
   */
  createTempSession(): void {
    const id = crypto.randomUUID();

    this.sessions.update((s: Record<string, ChatSession>) => ({
      ...s,
      [id]: {
        id,
        title: 'New chat',
        messages: [],
      },
    }));

    this.currentSessionId.set(id);
    this.draftMessage.set(this.draftBySession()[id] ?? '');
  }

  /**
   * Delete a chat session
   * Automatically selects next available session
   */
  deleteSession(sessionId: string): void {
    this.log(`Deleting session: ${sessionId}`);
    const wasActive = this.currentSessionId() === sessionId;

    this.chatApi.deleteSession(sessionId).subscribe({
      next: () => {
        this.log(`Session deleted: ${sessionId}`);
        this.sessions.update((s: Record<string, ChatSession>) => {
          const copy = { ...s };
          delete copy[sessionId];
          return copy;
        });
        this.draftBySession.update((drafts: Record<string, string>) => {
          const copy = { ...drafts };
          delete copy[sessionId];
          return copy;
        });

        // Select another session if deleted one was active
        if (wasActive) {
          const next = this.sessionIds()[0] ?? null;
          this.currentSessionId.set(next);
          this.draftMessage.set(next ? (this.draftBySession()[next] ?? '') : '');
        }
      },
      error: (err: unknown) => {
        this.logError(`Failed to delete session ${sessionId}: ${err}`);
        this.error.set('Failed to delete session');
      },
    });
  }

  /**
   * Rename a chat session
   * Optimistically updates UI, syncs with backend
   */
  renameSession(id: string, title: string): void {
    this.sessions.update((s: Record<string, ChatSession>) => ({
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

  /**
   * Reorder sessions (for drag-and-drop in sidebar)
   * Syncs order with backend for persistence
   */
  reorderSessions(sessions: ChatSession[]): void {
    const map: Record<string, ChatSession> = {};
    for (const s of sessions) {
      map[s.id] = s;
    }
    this.sessions.set(map);

    const sessionIds = sessions.map((s: ChatSession) => s.id);
    this.chatApi.reorderSessions(sessionIds).subscribe({
      error: () => {
        this.error.set('Failed to reorder sessions');
      },
    });
  }

  /**
   * Message Operations
   * Sending and managing chat messages
   */

  /**
   * Create a message object with timestamp
   */
  private createMessage(
    role: 'user' | 'assistant',
    content: string,
    attachment?: { filename: string; content: string },
  ): ChatMessage {
    return {
      role,
      content,
      created_at: new Date().toISOString(),
      attachment: attachment
        ? { filename: attachment.filename, content: attachment.content }
        : undefined,
    };
  }

  // SSE streaming control and retry logic
  stopStreaming: (() => void) | null = null;
  private messageRetryCount = 0;
  private maxRetries = 3;

  sendMessage(content: string, attachment?: { filename: string; content: string }): void {
    if (!content.trim()) return;

    const tempId = this.currentSessionId();
    if (!tempId) return;

    const tempSession = this.sessions()[tempId];

    const isTempSession =
      !tempSession || (tempSession.title === 'New chat' && tempSession.messages.length === 0);

    const generatedTitle = content.split('\n')[0].slice(0, 40);

    this.log(`Sending message to session ${tempId}, length: ${content.length}`);

    this.loading.set(true);
    this.error.set('');
    this.messageRetryCount = 0;

    const startStreaming = (sessionId: string) => {
      const startSse = () => {
        const session = this.sessions()[sessionId] ?? {
          id: sessionId,
          title: generatedTitle,
          messages: [],
        };

        this.sessions.update((s: Record<string, ChatSession>) => ({
          ...s,
          [sessionId]: {
            ...session,
            messages: [...session.messages, this.createMessage('user', content, attachment)],
          },
        }));

        let assistantIndex = -1;
        this.sessions.update((s: Record<string, ChatSession>) => {
          assistantIndex = s[sessionId].messages.length;
          return {
            ...s,
            [sessionId]: {
              ...s[sessionId],
              messages: [...s[sessionId].messages, this.createMessage('assistant', '')],
            },
          };
        });

        // real SSE streaming
        this.stopStreaming = this.chatApi.streamMessage(
          sessionId,
          content,
          this.currentModel().id,
          (token: string) => {
            this.sessions.update((s: Record<string, ChatSession>) => {
              const msgs = [...s[sessionId].messages];
              msgs[assistantIndex] = {
                ...msgs[assistantIndex],
                content: msgs[assistantIndex].content + token,
              };
              return { ...s, [sessionId]: { ...s[sessionId], messages: msgs } };
            });
          },

          (reasoning: string) => {
            this.sessions.update((s: Record<string, ChatSession>) => {
              const msgs = [...s[sessionId].messages];

              // Append reasoning token (incremental streaming)
              const currentReasoning = msgs[assistantIndex].meta?.reasoning || '';
              msgs[assistantIndex] = {
                ...msgs[assistantIndex],
                meta: {
                  ...(msgs[assistantIndex].meta ?? {}),
                  reasoning: currentReasoning + reasoning,
                  reasoning_streaming: true,
                },
              };

              return {
                ...s,
                [sessionId]: {
                  ...s[sessionId],
                  messages: msgs,
                },
              };
            });
          },
          () => {
            this.log(`Message streaming completed for session ${sessionId}`);
            this.loading.set(false);
            this.stopStreaming = null;
            this.messageRetryCount = 0;

            this.sessions.update((s: Record<string, ChatSession>) => {
              const msgs = [...s[sessionId].messages];
              msgs[assistantIndex] = {
                ...msgs[assistantIndex],
                meta: {
                  ...(msgs[assistantIndex].meta ?? {}),
                  reasoning_streaming: false,
                },
              };
              return { ...s, [sessionId]: { ...s[sessionId], messages: msgs } };
            });

            this.memoryStore.reload(sessionId);
          },
          (metadata: MessageMetadata) => {
            // Handle metadata from backend
            this.setLastMessageMetadata(metadata);

            // Update message with metadata
            this.sessions.update((s: Record<string, ChatSession>) => {
              const msgs = [...s[sessionId].messages];
              msgs[assistantIndex] = {
                ...msgs[assistantIndex],
                meta: {
                  ...(msgs[assistantIndex].meta ?? {}),
                  ...metadata,
                },
              };
              return { ...s, [sessionId]: { ...s[sessionId], messages: msgs } };
            });
          },
          (status: { type: string; data?: any }) => {
            // Handle verification status updates
            switch (status.type) {
              case 'answer_complete':
                this.verificationStatus.set({ type: 'verifying', message: 'Verifying answer...' });
                break;
              case 'verification_complete':
                this.verificationStatus.set({
                  type: 'verified',
                  message: `Risk: ${status.data?.risk_level || 'NONE'}`,
                  data: status.data,
                });
                break;
              case 'reasoning_starting':
                this.verificationStatus.set({
                  type: 'verifying',
                  message: 'Generating reasoning...',
                });
                break;
            }
          },
          this.reasoningEnabled(),
        );
      };

      if (attachment && attachment.content) {
        this.chatApi.attachFile(sessionId, attachment).subscribe({
          next: () => startSse(),
          error: (err: unknown) => {
            this.logError(`Failed to attach file: ${err}`);
            this.error.set('Failed to attach file');
            this.loading.set(false);
          },
        });
        return;
      }

      startSse();
    };

    if (isTempSession) {
      this.chatApi.createSession(generatedTitle).subscribe({
        next: (session: ChatSession) => {
          this.log(`New session created: ${session.id}`);
          this.sessions.update((s: Record<string, ChatSession>) => {
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
        error: (err: unknown) => {
          this.logError(`Failed to create session: ${err}`);
          // Retry logic
          if (this.messageRetryCount < this.maxRetries) {
            this.messageRetryCount++;
            this.log(
              `Retrying session creation: attempt ${this.messageRetryCount} of ${this.maxRetries}`,
            );
            setTimeout(() => this.sendMessage(content, attachment), 1000);
          } else {
            this.error.set('Failed to create session');
            this.loading.set(false);
          }
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

  removeMessagesFrom(startIndex: number): void {
    const sessionId = this.currentSessionId();
    if (!sessionId) return;

    this.sessions.update((s: Record<string, ChatSession>) => {
      const session = s[sessionId];
      if (!session) return s;

      return {
        ...s,
        [sessionId]: {
          ...session,
          messages: session.messages.slice(0, startIndex),
        },
      };
    });
  }

  rememberMessage(message: ChatMessage): void {
    const sessionId = this.currentSessionId();
    if (!sessionId || !message?.content || message.remembered) return;

    this.memoryStore.addManual(message.content);

    this.sessions.update((sessions: Record<string, ChatSession>) => {
      const session = sessions[sessionId];
      if (!session) return sessions;

      const updatedMessages = session.messages.map((m) =>
        m.created_at === message.created_at ? { ...m, remembered: true } : m,
      );

      return {
        ...sessions,
        [sessionId]: {
          ...session,
          messages: updatedMessages,
        },
      };
    });
  }

  /**
   * state
   */

  loadLatestMessages(sessionId: string): void {
    const session = this.sessions()[sessionId];
    if (!session) return;

    if (session.messages.length) return;

    this.sessions.update((s: Record<string, ChatSession>) => ({
      ...s,
      [sessionId]: {
        ...s[sessionId],
        loadingMore: true,
      },
    }));

    this.chatApi.getMessages(sessionId, 20).subscribe({
      next: (msgs: ChatMessage[]) => {
        this.sessions.update((s: Record<string, ChatSession>) => ({
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
        this.sessions.update((s: Record<string, ChatSession>) => ({
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

    this.sessions.update((s: Record<string, ChatSession>) => ({
      ...s,
      [sessionId]: {
        ...s[sessionId],
        loadingMore: true,
      },
    }));

    this.chatApi.getMessages(sessionId, 20, before).subscribe({
      next: (older: ChatMessage[]) => {
        this.sessions.update((s: Record<string, ChatSession>) => ({
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
        this.sessions.update((s: Record<string, ChatSession>) => ({
          ...s,
          [sessionId]: {
            ...s[sessionId],
            loadingMore: false,
          },
        }));
      },
    });
  }

  /* ============================
   *  Helpers
   * ============================ */

  private pushUserMessage(id: string, content: string) {
    this.sessions.update((s: Record<string, ChatSession>) => ({
      ...s,
      [id]: {
        ...s[id],
        messages: [...s[id].messages, this.createMessage('user', content)],
      },
    }));
  }

  private pushAssistantMessage(id: string, content: string) {
    this.sessions.update((s: Record<string, ChatSession>) => ({
      ...s,
      [id]: {
        ...s[id],
        messages: [...s[id].messages, this.createMessage('assistant', content)],
      },
    }));
  }
}

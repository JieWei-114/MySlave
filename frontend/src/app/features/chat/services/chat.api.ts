/**
 * Chat API Service
 * Includes both REST API calls and Server-Sent Events (SSE) for streaming
 */
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';

import { AppConfigService } from '../../../core/services/app-config.services';
import { ChatSession, ChatSessionDto } from './chat.model';

@Injectable({ providedIn: 'root' })
export class ChatApi {
  private http = inject(HttpClient);
  private config = inject(AppConfigService);

  /**
   * Send a message to a chat session (non-streaming)
   */
  sendMessage(sessionId: string, content: string) {
    return this.http.post<{ reply: string }>(
      `${this.config.apiBaseUrl}/chat/${sessionId}/message`,
      { content },
    );
  }

  /**
   * Get all chat sessions (metadata only, no messages)
   */
  getSessions() {
    return this.http.get<ChatSessionDto[]>(`${this.config.apiBaseUrl}/chat/sessions`);
  }

  /**
   * Get full session data including messages
   */
  getSessionbyId(sessionId: string) {
    return this.http.get<any>(`${this.config.apiBaseUrl}/chat/${sessionId}`);
  }

  /**
   * Create a new chat session
   */
  createSession(title = 'New chat') {
    return this.http.post<ChatSession>(`${this.config.apiBaseUrl}/chat/session`, { title });
  }

  /**
   * Rename an existing chat session
   */
  renameSession(sessionId: string, title: string) {
    return this.http.patch<{ id: string; title: string }>(
      `${this.config.apiBaseUrl}/chat/${sessionId}/rename`,
      { title },
    );
  }

  /**
   * Delete a chat session permanently
   */
  deleteSession(sessionId: string) {
    return this.http.delete(`${this.config.apiBaseUrl}/chat/${sessionId}`);
  }

  /**
   * Reorder chat sessions (for sidebar drag-and-drop)
   */
  reorderSessions(sessionIds: string[]) {
    return this.http.post<void>(`${this.config.apiBaseUrl}/chat/reorder`, { sessionIds });
  }

  /**
   * Stream AI response in real-time using Server-Sent Events (SSE)
   * Uses GET request with query parameters (not POST)
   */
  streamMessage(
    sessionId: string,
    content: string,
    model: string,
    onToken: (t: string) => void,
    onReasoning: (r: string) => void,
    onDone: () => void,
    onMetadata?: (meta: any) => void,
    onVerification?: (status: { type: string; data?: any }) => void,
    reasoningEnabled: boolean = false,
  ): () => void {
    let url =
      `${this.config.apiBaseUrl}/chat/${sessionId}/stream` +
      `?content=${encodeURIComponent(content)}` +
      `&model=${encodeURIComponent(model)}` +
      `&reasoning=${reasoningEnabled}`;

    const es = new EventSource(url);

    // Token streaming (answer)
    es.addEventListener('token', (e: MessageEvent) => {
      const token = JSON.parse(e.data);
      onToken(token);
    });

    // Answer streaming complete
    es.addEventListener('answer_complete', (e: MessageEvent) => {
      if (onVerification) {
        onVerification({ type: 'answer_complete' });
      }
    });

    // Verification starting
    es.addEventListener('verification_starting', (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      if (onVerification) {
        onVerification({ type: 'verification_starting', data });
      }
    });

    // Verification complete
    es.addEventListener('verification_complete', (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      if (onVerification) {
        onVerification({ type: 'verification_complete', data });
      }
    });

    // Reasoning starting
    es.addEventListener('reasoning_starting', (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      if (onVerification) {
        onVerification({ type: 'reasoning_starting', data });
      }
    });

    // Reasoning tokens
    es.addEventListener('reasoning_token', (e: MessageEvent) => {
      const token = JSON.parse(e.data);
      onReasoning(token);
    });

    // Done with metadata
    es.addEventListener('done', (e: MessageEvent) => {
      const payload = JSON.parse(e.data);

      if (payload.reasoning) {
        onReasoning(payload.reasoning);
      }

      if (payload.metadata && onMetadata) {
        onMetadata(payload.metadata);
      }

      es.close();
      onDone();
    });

    es.onerror = (err) => {
      console.error('SSE error', err);
      es.close();
      onDone();
    };

    return () => es.close();
  }

  /**
   * Get messages from a session with pagination
   */
  getMessages(sessionId: string, limit = 20, before?: string) {
    let url = `${this.config.apiBaseUrl}/chat/${sessionId}/messages?limit=${limit}`;
    if (before) {
      url += `&before=${encodeURIComponent(before)}`;
    }
    return this.http.get<any[]>(url);
  }

  /**
   * Attach a file to the current chat session
   */
  attachFile(sessionId: string, payload: { filename: string; content: string }) {
    return this.http.post<{ status: string; filename: string; length: number }>(
      `${this.config.apiBaseUrl}/chat/${sessionId}/attachment`,
      payload,
    );
  }
}

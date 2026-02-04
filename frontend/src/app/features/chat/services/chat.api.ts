import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';

import { AppConfigService } from '../../../core/services/app-config.services';
import { ChatSession, ChatSessionDto } from './chat.model';

@Injectable({ providedIn: 'root' })
export class ChatApi {
  private http = inject(HttpClient);
  private config = inject(AppConfigService);

  sendMessage(sessionId: string, content: string) {
    return this.http.post<{ reply: string }>(
      `${this.config.apiBaseUrl}/chat/${sessionId}/message`,
      { content },
    );
  }

  getSessions() {
    return this.http.get<ChatSessionDto[]>(`${this.config.apiBaseUrl}/chat/sessions`);
  }

  getSessionbyId(sessionId: string) {
    return this.http.get<any>(`${this.config.apiBaseUrl}/chat/${sessionId}`);
  }

  createSession(title = 'New chat') {
    return this.http.post<ChatSession>(`${this.config.apiBaseUrl}/chat/session`, { title });
  }

  renameSession(sessionId: string, title: string) {
    return this.http.patch<{ id: string; title: string }>(
      `${this.config.apiBaseUrl}/chat/${sessionId}/rename`,
      { title },
    );
  }

  deleteSession(sessionId: string) {
    return this.http.delete(`${this.config.apiBaseUrl}/chat/${sessionId}`);
  }

  reorderSessions(sessionIds: string[]) {
    return this.http.post<void>(`${this.config.apiBaseUrl}/chat/reorder`, { sessionIds });
  }

  streamMessage(
    sessionId: string,
    content: string,
    model: string,
    onToken: (t: string) => void,
    onReasoning: (r: string) => void,
    onDone: () => void,
  ): () => void {
    const url =
      `${this.config.apiBaseUrl}/chat/${sessionId}/stream` +
      `?content=${encodeURIComponent(content)}` +
      `&model=${encodeURIComponent(model)}`;

    const es = new EventSource(url);

    // es.onmessage = (e) => {
    //   const token = decodeURIComponent(e.data);
    //   onToken(token);
    // };

    es.addEventListener('token', (e: MessageEvent) => {
      const token = JSON.parse(e.data);
      onToken(token);
    });

    es.addEventListener('done', (e: MessageEvent) => {
      const payload = JSON.parse(e.data);

      if (payload.reasoning) {
        onReasoning(payload.reasoning);
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

  getMessages(sessionId: string, limit = 20, before?: string) {
    let url = `${this.config.apiBaseUrl}/chat/${sessionId}/messages?limit=${limit}`;
    if (before) {
      url += `&before=${encodeURIComponent(before)}`;
    }
    return this.http.get<any[]>(url);
  }

  attachFile(sessionId: string, payload: { filename: string; content: string }) {
    return this.http.post<{ status: string; filename: string; length: number }>(
      `${this.config.apiBaseUrl}/chat/${sessionId}/attachment`,
      payload,
    );
  }
}

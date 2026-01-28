import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

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

  streamMessage(
    sessionId: string,
    content: string,
    model: string,
    onToken: (t: string) => void,
    onDone: () => void,
  ): () => void {
    const url =
      `${this.config.apiBaseUrl}/chat/${sessionId}/stream` +
      `?content=${encodeURIComponent(content)}` +
      `&model=${encodeURIComponent(model)}`;

    const es = new EventSource(url);

    es.onmessage = (e) => {
      const token = decodeURIComponent(e.data);
      onToken(token);
    };

    es.addEventListener('done', () => {
      es.close();
      onDone();
    });

    es.onerror = () => {
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
}

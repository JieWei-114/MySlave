import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { AppConfigService } from '../../../core/services/app-config.services';

@Injectable({ providedIn: 'root' })
export class MemoryApi {
  private http = inject(HttpClient);
  private config = inject(AppConfigService);

  addMemory(content: string, chatSessionId: string) {
    return this.http.post(`${this.config.apiBaseUrl}/memory/`, {
      content,
      chat_sessionId: chatSessionId,
    });
  }

  getMemories(chatSessionId: string) {
    return this.http.get<any[]>(
      `${this.config.apiBaseUrl}/memory/?chat_sessionId=${chatSessionId}`,
    );
  }

  enable(id: string) {
    return this.http.patch(`${this.config.apiBaseUrl}/memory/${id}/enable`, {});
  }

  disable(id: string) {
    return this.http.patch(`${this.config.apiBaseUrl}/memory/${id}/disable`, {});
  }

  delete(id: string) {
    return this.http.delete(`${this.config.apiBaseUrl}/memory/${id}`);
  }

  search(chatSessionId: string, q: string) {
    return this.http.get<any[]>(
      `${this.config.apiBaseUrl}/memory/search?chat_sessionId=${chatSessionId}&q=${encodeURIComponent(q)}`,
    );
  }

  compress(chatSessionId: string, model: string) {
    return this.http.post(
      `${this.config.apiBaseUrl}/memory/compress?chat_sessionId=${chatSessionId}&model=${model}`,
      {},
    );
  }
}

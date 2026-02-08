/**
 * Memory API Service
 */
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { AppConfigService } from '../../../core/services/app-config.services';

@Injectable({ providedIn: 'root' })
export class MemoryApi {
  private http = inject(HttpClient);
  private config = inject(AppConfigService);

  /**
   * Create a new memory item
   */
  addMemory(content: string, sessionId: string, category?: string) {
    return this.http.post(`${this.config.apiBaseUrl}/memory/`, {
      content,
      session_id: sessionId,
      category,
    });
  }

  /**
   * Get all enabled memories for a session
   */
  getMemories(sessionId: string) {
    return this.http.get<any[]>(`${this.config.apiBaseUrl}/memory/?session_id=${sessionId}`);
  }

  /**
   * Enable a memory for use in context selection
   */
  enable(id: string) {
    return this.http.patch(`${this.config.apiBaseUrl}/memory/${id}/enable`, {});
  }

  /**
   * Disable a memory without deleting it
   */
  disable(id: string) {
    return this.http.patch(`${this.config.apiBaseUrl}/memory/${id}/disable`, {});
  }

  /**
   * Permanently delete a memory item
   */
  delete(id: string) {
    return this.http.delete(`${this.config.apiBaseUrl}/memory/${id}`);
  }

  /**
   * Semantic search for memories using embeddings
   * Finds memories related to query using vector similarity.
   * More accurate than keyword search for finding relevant context.
   */
  search(sessionId: string, q: string) {
    return this.http.get<any[]>(
      `${this.config.apiBaseUrl}/memory/search?session_id=${sessionId}&q=${encodeURIComponent(q)}`,
    );
  }

  /**
   * Compress and consolidate memories for a session
   * Uses LLM to summarize, deduplicate, and improve memory relevance.
   */
  compress(sessionId: string, model: string) {
    return this.http.post(
      `${this.config.apiBaseUrl}/memory/compress?session_id=${sessionId}&model=${model}`,
      {},
    );
  }
}

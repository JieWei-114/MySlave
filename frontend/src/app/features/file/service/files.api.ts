/**
 * Files API Service
 */
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';

import { AppConfigService } from '../../../core/services/app-config.services';
import { FileAttachment } from './files.model';

@Injectable({ providedIn: 'root' })
export class FilesApi {
  private http = inject(HttpClient);
  private config = inject(AppConfigService);

  listFiles(sessionId: string) {
    return this.http.get<FileAttachment[]>(`${this.config.apiBaseUrl}/chat/${sessionId}/files`);
  }

  deleteFile(sessionId: string, fileId: string) {
    return this.http.delete(`${this.config.apiBaseUrl}/chat/${sessionId}/files/${fileId}`);
  }

  uploadFile(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<{ content: string; filename: string }>(
      `${this.config.apiBaseUrl}/chat/upload`,
      formData,
    );
  }

  attachFile(sessionId: string, payload: { filename: string; content: string }) {
    return this.http.post<{ status: string; filename: string; length: number }>(
      `${this.config.apiBaseUrl}/chat/${sessionId}/attachment`,
      payload,
    );
  }
}

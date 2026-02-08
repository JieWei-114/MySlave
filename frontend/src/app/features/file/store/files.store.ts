/**
 * Files Store
 * Manages file attachments per session
 */
import { Injectable, signal, inject } from '@angular/core';
import { FilesApi } from '../service/files.api';
import { FileAttachment } from '../service/files.model';

@Injectable({ providedIn: 'root' })
export class FilesStore {
  files = signal<FileAttachment[]>([]);
  loading = signal(false);
  error = signal('');
  uploading = signal(false);

  private api = inject(FilesApi);
  readonly currentSessionId = signal<string | null>(null);

  load(sessionId: string) {
    this.currentSessionId.set(sessionId);
    this.loading.set(true);
    this.api.listFiles(sessionId).subscribe({
      next: (list) => {
        this.files.set(list || []);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('Failed to load files');
        this.loading.set(false);
      },
    });
  }

  delete(sessionId: string, fileId: string) {
    this.api.deleteFile(sessionId, fileId).subscribe({
      next: () => {
        this.files.update((list) => list.filter((f) => f.id !== fileId));
      },
      error: () => this.error.set('Failed to delete file'),
    });
  }

  refresh() {
    const sessionId = this.currentSessionId();
    if (!sessionId) return;
    this.load(sessionId);
  }
}
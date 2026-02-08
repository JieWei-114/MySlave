/**
 * Files Panel
 * Manage file attachments per session
 */
import { Component, Input, effect, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { FilesStore } from '../store/files.store';
import { FilesApi } from '../service/files.api';
import { AppConfigService } from '../../../core/services/app-config.services';
import { AppButtonComponent } from '../../../shared/ui/button/app-button.component';

@Component({
  selector: 'app-files-panel',
  standalone: true,
  imports: [CommonModule, FormsModule, AppButtonComponent],
  templateUrl: './files.page.html',
  styleUrls: ['./files.page.css'],
})
export class FilesPage {
  private _sessionId = signal<string | null>(null);
  selectedFileName = signal('');
  fileError = signal('');

  @Input({ required: true })
  set sessionId(value: string) {
    this._sessionId.set(value);
  }

  constructor(
    public fileStore: FilesStore,
    private api: FilesApi,
    private config: AppConfigService,
  ) {
    effect(() => {
      const id = this._sessionId();
      if (!id) return;
      this.fileStore.load(id);
    });
  }

  onFileSelected(event: Event): void {
    this.fileError.set('');
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;

    const maxBytes = this.config.fileUploadMaxBytes;
    if (file.size > maxBytes) {
      this.fileError.set('File too large.');
      input.value = '';
      return;
    }

    const isBinary = this.config.binaryExtensions.some((ext) =>
      file.name.toLowerCase().endsWith(ext),
    );

    const sessionId = this._sessionId();
    if (!sessionId) return;

    if (isBinary) {
      this.fileStore.uploading.set(true);
      this.api.uploadFile(file).subscribe({
        next: (res) => {
          this.api
            .attachFile(sessionId, { filename: res.filename, content: res.content })
            .subscribe({
              next: () => {
                this.fileStore.uploading.set(false);
                this.selectedFileName.set(res.filename);
                this.fileStore.refresh();
              },
              error: () => {
                this.fileStore.uploading.set(false);
                this.fileError.set('Failed to attach file.');
              },
            });
        },
        error: () => {
          this.fileStore.uploading.set(false);
          this.fileError.set('Failed to extract file content.');
        },
      });
      input.value = '';
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      const content = String(reader.result ?? '').trim();
      if (!content) {
        this.fileError.set('File is empty or unreadable.');
        input.value = '';
        return;
      }

      this.api.attachFile(sessionId, { filename: file.name, content }).subscribe({
        next: () => {
          this.selectedFileName.set(file.name);
          this.fileStore.refresh();
        },
        error: () => {
          this.fileError.set('Failed to attach file.');
        },
      });
      input.value = '';
    };

    reader.onerror = () => {
      this.fileError.set('Failed to read file.');
      input.value = '';
    };

    reader.readAsText(file);
  }

  deleteFile(fileId: string): void {
    const sessionId = this._sessionId();
    if (!sessionId) return;
    this.fileStore.delete(sessionId, fileId);
  }
}
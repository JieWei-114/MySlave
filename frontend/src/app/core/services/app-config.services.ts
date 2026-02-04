import { Injectable } from '@angular/core';

export interface ClientConfig {
  fileUpload: {
    maxSizeMB: number;
    allowedBinaryExtensions: string[];
    maxExtractChars: number;
  };
}

@Injectable({ providedIn: 'root' })
export class AppConfigService {
  readonly appName = 'MySlave';
  readonly apiBaseUrl = 'http://127.0.0.1:8000';
  readonly wsUrl = 'ws://127.0.0.1:8000';

  private clientConfig!: ClientConfig;

  async load(): Promise<void> {
    this.clientConfig = await fetch(`${this.apiBaseUrl}/client-config`)
      .then(res => res.json());
  }

  get fileUploadMaxBytes(): number {
    return this.clientConfig
      ? this.clientConfig.fileUpload.maxSizeMB * 1024 * 1024
      : 10 * 1024 * 1024; // fallback
  }

  get binaryExtensions(): string[] {
    return this.clientConfig
      ? this.clientConfig.fileUpload.allowedBinaryExtensions
      : ['.pdf', '.doc', '.docx'];
  }

  get fileUploadMaxMB(): number {
    return this.clientConfig.fileUpload.maxSizeMB;
  }
}

import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { AppConfigService } from '../../../core/services/app-config.services';

@Injectable({ providedIn: 'root' })
export class ToolsApi {
  constructor(private http: HttpClient, private config: AppConfigService) {}

  webSearch(q: string) {
    return this.http.get<any>(
      `${this.config.apiBaseUrl}/tools/web-search?q=${encodeURIComponent(q)}`
    );
  }
}

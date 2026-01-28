import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AppConfigService } from '../../../core/services/app-config.services';
import { QuotaInfo, WebSearchResponse } from './web.model';

@Injectable({ providedIn: 'root' })
export class WebApi {
  private http = inject(HttpClient);
  private config = inject(AppConfigService);

  webSearch(q: string): Observable<WebSearchResponse> {
    return this.http.get<WebSearchResponse>(
      `${this.config.apiBaseUrl}/web/web-search?q=${encodeURIComponent(q)}`,
    );
  }

  getQuotas(): Observable<QuotaInfo> {
    return this.http.get<QuotaInfo>(`${this.config.apiBaseUrl}/web/quotas`);
  }
}
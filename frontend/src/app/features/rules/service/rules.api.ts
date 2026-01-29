import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { AppConfigService } from '../../../core/services/app-config.services';
import { RulesConfig } from './rules.model';

@Injectable({
  providedIn: 'root',
})
export class RulesApiService {
  private http = inject(HttpClient);
  private config = inject(AppConfigService);
  private apiUrl = `${this.config.apiBaseUrl}/rules`;

  getRules(): Observable<RulesConfig> {
    return this.http.get<RulesConfig>(this.apiUrl);
  }

  updateRules(rules: RulesConfig): Observable<RulesConfig> {
    return this.http.put<RulesConfig>(this.apiUrl, rules);
  }
}
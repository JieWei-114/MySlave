import { Injectable } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class AppConfigService {
  readonly appName = 'MySlave';
  readonly apiBaseUrl = 'http://127.0.0.1:8000';
  readonly wsUrl = 'ws://127.0.0.1:8000';
}

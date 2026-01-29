import { Component, OnInit, OnDestroy, ChangeDetectionStrategy, effect } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { ChatStore } from '../../chat/store/chat.store';
import { WebApi } from '../service/web.api';
import { QuotaInfo, WebSearchResult } from '../service/web.model';
import { AppButtonComponent } from '../../../shared/ui/button/app-button.component';
import { WebStore } from '../store/web.store';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { signal } from '@angular/core';

@Component({
  selector: 'app-web-search',
  standalone: true,
  imports: [FormsModule, CommonModule, AppButtonComponent],
  templateUrl: './web-search.component.html',
  styleUrls: ['./web-search.component.css'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class WebSearchComponent implements OnInit, OnDestroy {
  q = signal('');
  results = signal<WebSearchResult[]>([]);
  quotas = signal<QuotaInfo | null>(null);
  loading = signal(false);

  private destroy$ = new Subject<void>();

  constructor(
    private api: WebApi,
    private chatStore: ChatStore,
    private webStore: WebStore,
  ) {
    // Watch for session changes and update web search results
    effect(() => {
      const sessionId = this.chatStore.currentSessionId();
      if (sessionId) {
        const state = this.webStore.getState();
        this.q.set(state.q);
        this.results.set(state.results);
        this.quotas.set(state.quotas);
        this.loading.set(state.loading);
      }
    });
  }

  ngOnInit(): void {
    // Initialize from store for current session
    const state = this.webStore.getState();
    this.q.set(state.q);
    this.results.set(state.results);
    this.quotas.set(state.quotas);
    this.loading.set(state.loading);

    this.loadQuotas();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadQuotas(): void {
    this.api
      .getQuotas()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (quotas) => {
          this.quotas.set(quotas);
          this.webStore.setQuotas(quotas);
        },
        error: () => {
          this.quotas.set(null);
          this.webStore.setQuotas(null);
        },
      });
  }

  search() {
    const query = this.q();
    if (!query.trim()) return;

    this.loading.set(true);
    this.webStore.setLoading(true);
    this.webStore.setQuery(query);

    const sessionId = this.chatStore.currentSessionId();

    this.api
      .webSearch(query, sessionId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (res) => {
          const newResults = res.results ?? [];
          const newQuotas = res.quotas ?? null;

          this.results.set(newResults);
          this.quotas.set(newQuotas);
          this.loading.set(false);

          this.webStore.setResults(newResults);
          this.webStore.setQuotas(newQuotas);
          this.webStore.setLoading(false);
        },
        error: () => {
          this.loading.set(false);
          this.webStore.setLoading(false);
        },
      });
  }

  insert(r: any) {
    this.chatStore.appendToDraft(`Web result:\n${r.title}\n${r.snippet}\n${r.link}`);
  }
}

import { Injectable, inject } from '@angular/core';
import { signal, computed } from '@angular/core';
import { ChatStore } from '../../chat/store/chat.store';
import { QuotaInfo, WebSearchResult, WebState } from '../service/web.model';

const initialState: WebState = {
  q: '',
  results: [],
  quotas: null,
  loading: false,
};

@Injectable({ providedIn: 'root' })
export class WebStore {
  private chatStore = inject(ChatStore);

  // Per-session state storage
  private sessionWebStates = signal<Record<string, WebState>>({});

  // Current session context
  readonly currentSessionId = computed(() => this.chatStore.currentSessionId());

  // Computed signals for current session
  readonly q = computed(() => {
    const sessionId = this.currentSessionId();
    return sessionId ? (this.sessionWebStates()[sessionId]?.q ?? '') : '';
  });

  readonly results = computed(() => {
    const sessionId = this.currentSessionId();
    return sessionId ? (this.sessionWebStates()[sessionId]?.results ?? []) : [];
  });

  readonly quotas = computed(() => {
    const sessionId = this.currentSessionId();
    return sessionId ? (this.sessionWebStates()[sessionId]?.quotas ?? null) : null;
  });

  readonly loading = computed(() => {
    const sessionId = this.currentSessionId();
    return sessionId ? (this.sessionWebStates()[sessionId]?.loading ?? false) : false;
  });

  constructor() {
    this.loadFromLocalStorage();
  }

  getState(): WebState {
    const sessionId = this.currentSessionId();
    if (!sessionId) return initialState;
    return this.sessionWebStates()[sessionId] ?? initialState;
  }

  setQuery(q: string): void {
    const sessionId = this.currentSessionId();
    if (!sessionId) return;

    const states = this.sessionWebStates();
    const state = states[sessionId] ?? { ...initialState };
    state.q = q;

    states[sessionId] = { ...state };
    this.sessionWebStates.set({ ...states });
    this.saveToLocalStorage();
  }

  setResults(results: WebSearchResult[]): void {
    const sessionId = this.currentSessionId();
    if (!sessionId) return;

    const states = this.sessionWebStates();
    const state = states[sessionId] ?? { ...initialState };
    state.results = results;

    states[sessionId] = { ...state };
    this.sessionWebStates.set({ ...states });
    this.saveToLocalStorage();
  }

  setQuotas(quotas: QuotaInfo | null): void {
    const sessionId = this.currentSessionId();
    if (!sessionId) return;

    const states = this.sessionWebStates();
    const state = states[sessionId] ?? { ...initialState };
    state.quotas = quotas;

    states[sessionId] = { ...state };
    this.sessionWebStates.set({ ...states });
    this.saveToLocalStorage();
  }

  setLoading(loading: boolean): void {
    const sessionId = this.currentSessionId();
    if (!sessionId) return;

    const states = this.sessionWebStates();
    const state = states[sessionId] ?? { ...initialState };
    state.loading = loading;

    states[sessionId] = { ...state };
    this.sessionWebStates.set({ ...states });
  }

  clearResults(): void {
    const sessionId = this.currentSessionId();
    if (!sessionId) return;

    const states = this.sessionWebStates();
    const state = states[sessionId] ?? { ...initialState };
    state.results = [];

    states[sessionId] = { ...state };
    this.sessionWebStates.set({ ...states });
    this.saveToLocalStorage();
  }

  private saveToLocalStorage(): void {
    try {
      localStorage.setItem('webSearchState', JSON.stringify(this.sessionWebStates()));
    } catch (e) {
      console.error('Failed to save web search state', e);
    }
  }

  private loadFromLocalStorage(): void {
    try {
      const saved = localStorage.getItem('webSearchState');
      if (saved) {
        const states = JSON.parse(saved);
        this.sessionWebStates.set(states);
      }
    } catch (e) {
      console.error('Failed to load web search state', e);
    }
  }

  reset(): void {
    this.sessionWebStates.set({});
    localStorage.removeItem('webSearchState');
  }
}

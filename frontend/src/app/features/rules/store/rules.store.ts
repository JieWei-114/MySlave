import { Injectable, signal, computed, inject } from '@angular/core';
import { RulesApiService } from '../service/rules.api';
import { RulesConfig } from '../service/rules.model';

@Injectable({ providedIn: 'root' })
export class RulesStore {
  private rulesApi = inject(RulesApiService);

  /* ============================
   *  Session Rules State
   * ============================ */

  private sessionRules = signal<Record<string, RulesConfig>>({});
  private sessionLoading = signal<Record<string, boolean>>({});
  private sessionError = signal<Record<string, string>>({});
  private sessionSaved = signal<Record<string, boolean>>({});

  // Current session context
  readonly currentSessionId = signal<string | null>(null);

  /* ===============================
   *  Session Rules Computed
   * =============================== */

  readonly rules = computed(() => {
    const sessionId = this.currentSessionId();
    return sessionId && this.sessionRules()[sessionId] ? this.sessionRules()[sessionId] : null;
  });

  readonly loading = computed(() => {
    const sessionId = this.currentSessionId();
    return sessionId ? (this.sessionLoading()[sessionId] ?? false) : false;
  });

  readonly error = computed(() => {
    const sessionId = this.currentSessionId();
    return sessionId ? (this.sessionError()[sessionId] ?? '') : '';
  });

  readonly saved = computed(() => {
    const sessionId = this.currentSessionId();
    return sessionId ? (this.sessionSaved()[sessionId] ?? false) : false;
  });

  readonly searxngEnabled = computed(() => this.rules()?.searxng ?? false);
  readonly duckduckgoEnabled = computed(() => this.rules()?.duckduckgo ?? false);
  readonly tavilyEnabled = computed(() => this.rules()?.tavily ?? false);
  readonly serperEnabled = computed(() => this.rules()?.serper ?? false);
  readonly tavilyExtractEnabled = computed(() => this.rules()?.tavilyExtract ?? false);
  readonly localExtractEnabled = computed(() => this.rules()?.localExtract ?? false);
  readonly advanceSearchEnabled = computed(() => this.rules()?.advanceSearch ?? false);
  readonly advanceExtractEnabled = computed(() => this.rules()?.advanceExtract ?? false);

  // Effective rules for individual providers
  readonly effectiveSearchEnabled = computed(() => ({
    searxng: this.rules()?.searxng ?? false,
    duckduckgo: this.rules()?.duckduckgo ?? false,
    tavily: this.rules()?.tavily ?? false,
    serper: this.rules()?.serper ?? false,
  }));

  readonly effectiveExtractEnabled = computed(() => ({
    tavily: this.rules()?.tavilyExtract ?? false,
    local: this.rules()?.localExtract ?? false,
  }));

  /* ===============================
   *  Set the current session context
   * =============================== */

  setCurrentSession(sessionId: string | null): void {
    this.currentSessionId.set(sessionId);
    if (sessionId && !this.sessionRules()[sessionId]) {
      this.loadSessionRules(sessionId);
    }
  }

  /* ====================================
   *  Load rules for a specific session
   * ==================================== */

  loadSessionRules(sessionId: string): void {
    const loading = { ...this.sessionLoading() };
    loading[sessionId] = true;
    this.sessionLoading.set(loading);

    const errors = { ...this.sessionError() };
    errors[sessionId] = '';
    this.sessionError.set(errors);

    this.rulesApi.getSessionRules(sessionId).subscribe({
      next: (rulesData: RulesConfig) => {
        const rules = { ...this.sessionRules() };
        rules[sessionId] = rulesData;
        this.sessionRules.set(rules);

        const loadingUpdated = { ...this.sessionLoading() };
        loadingUpdated[sessionId] = false;
        this.sessionLoading.set(loadingUpdated);
      },
      error: (error: unknown) => {
        const errorMessage =
          error instanceof Error ? error.message : 'Failed to load session rules';
        const errors = { ...this.sessionError() };
        errors[sessionId] = errorMessage;
        this.sessionError.set(errors);

        const loadingUpdated = { ...this.sessionLoading() };
        loadingUpdated[sessionId] = false;
        this.sessionLoading.set(loadingUpdated);
      },
    });
  }

  /* ========================================
   *  Toggle a rule for the current session
   * ======================================== */

  toggleSessionRule(key: keyof RulesConfig): void {
    const sessionId = this.currentSessionId();
    if (!sessionId) return;

    const currentRules = this.rules();
    if (!currentRules) return;

    const updatedRules: RulesConfig = {
      ...currentRules,
      [key]: !currentRules[key],
    };

    // Handle advance search logic
    if (key === 'advanceSearch' && updatedRules.advanceSearch) {
      // When enabling advanceSearch, enable all search services
      updatedRules.searxng = true;
      updatedRules.duckduckgo = true;
      updatedRules.tavily = true;
      updatedRules.serper = true;
    } else if (['searxng', 'duckduckgo', 'tavily', 'serper'].includes(key) && !updatedRules[key]) {
      // When disabling any search service, disable advanceSearch
      updatedRules.advanceSearch = false;
    }

    // Handle advance extract logic
    if (key === 'advanceExtract' && updatedRules.advanceExtract) {
      // When enabling advanceExtract, enable all extract services
      updatedRules.tavilyExtract = true;
      updatedRules.localExtract = true;
    } else if (['tavilyExtract', 'localExtract'].includes(key) && !updatedRules[key]) {
      // When disabling any extract service, disable advanceExtract
      updatedRules.advanceExtract = false;
    }

    const rules = { ...this.sessionRules() };
    rules[sessionId] = updatedRules;
    this.sessionRules.set(rules);

    this.updateSessionRules(sessionId, updatedRules);
  }

  /* ====================================
   *  Update a numeric limit
   * ==================================== */

  updateLimit(
    key: 'webSearchLimit' | 'memorySearchLimit' | 'historyLimit' | 'fileUploadMaxChars',
    value?: number,
  ): void {
    const sessionId = this.currentSessionId();
    if (!sessionId) return;

    const currentRules = this.rules();
    if (!currentRules) return;

    const updatedRules: RulesConfig = {
      ...currentRules,
      [key]: value,
    };

    const rules = { ...this.sessionRules() };
    rules[sessionId] = updatedRules;
    this.sessionRules.set(rules);

    this.updateSessionRules(sessionId, updatedRules);
  }

  /* ====================================
   *  Update custom instructions
   * ==================================== */

  updateCustomInstructions(value: string): void {
    const sessionId = this.currentSessionId();
    if (!sessionId) return;

    const currentRules = this.rules();
    if (!currentRules) return;

    const updatedRules: RulesConfig = {
      ...currentRules,
      customInstructions: value || undefined,
    };

    const rules = { ...this.sessionRules() };
    rules[sessionId] = updatedRules;
    this.sessionRules.set(rules);

    this.updateSessionRules(sessionId, updatedRules);
  }

  /* ====================================
   *  Update rules for a specific session
   * ==================================== */

  updateSessionRules(sessionId: string, rules: RulesConfig): void {
    const loading = { ...this.sessionLoading() };
    loading[sessionId] = true;
    this.sessionLoading.set(loading);

    const errors = { ...this.sessionError() };
    errors[sessionId] = '';
    this.sessionError.set(errors);

    this.rulesApi.updateSessionRules(sessionId, rules).subscribe({
      next: (updatedRules: RulesConfig) => {
        const rulesUpdated = { ...this.sessionRules() };
        rulesUpdated[sessionId] = updatedRules;
        this.sessionRules.set(rulesUpdated);

        const loadingUpdated = { ...this.sessionLoading() };
        loadingUpdated[sessionId] = false;
        this.sessionLoading.set(loadingUpdated);

        const savedUpdated = { ...this.sessionSaved() };
        savedUpdated[sessionId] = true;
        this.sessionSaved.set(savedUpdated);

        setTimeout(() => {
          const savedReset = { ...this.sessionSaved() };
          savedReset[sessionId] = false;
          this.sessionSaved.set(savedReset);
        }, 2000);
      },
      error: (error: unknown) => {
        const errorMessage =
          error instanceof Error ? error.message : 'Failed to update session rules';
        const errorsUpdated = { ...this.sessionError() };
        errorsUpdated[sessionId] = errorMessage;
        this.sessionError.set(errorsUpdated);

        const loadingUpdated = { ...this.sessionLoading() };
        loadingUpdated[sessionId] = false;
        this.sessionLoading.set(loadingUpdated);
      },
    });
  }

  /* ====================================
   *  Clear cached session rules
   * ==================================== */

  clearSessionRules(sessionId: string): void {
    const rules = { ...this.sessionRules() };
    delete rules[sessionId];
    this.sessionRules.set(rules);

    const loading = { ...this.sessionLoading() };
    delete loading[sessionId];
    this.sessionLoading.set(loading);

    const errors = { ...this.sessionError() };
    delete errors[sessionId];
    this.sessionError.set(errors);
  }
}

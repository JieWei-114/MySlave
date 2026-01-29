import { Injectable, signal, computed, inject } from '@angular/core';
import { RulesApiService } from '../service/rules.api';
import { DEFAULT_RULES, RulesConfig } from '../service/rules.model';

@Injectable({ providedIn: 'root' })
export class RulesStore {
  private rulesApi = inject(RulesApiService);

  private rules = signal<RulesConfig>(DEFAULT_RULES);
  readonly loading = signal(false);
  readonly error = signal('');

  // Computed values for individual rules
  readonly searxngEnabled = computed(() => this.rules().searxng);
  readonly duckduckgoEnabled = computed(() => this.rules().duckduckgo);
  readonly tavilyEnabled = computed(() => this.rules().tavily);
  readonly serperEnabled = computed(() => this.rules().serper);
  readonly tavilyExtractEnabled = computed(() => this.rules().tavilyExtract);
  readonly localExtractEnabled = computed(() => this.rules().localExtract);

  constructor() {
    this.loadRules();
  }

  private loadRules(): void {
    this.loading.set(true);
    this.error.set('');

    this.rulesApi.getRules().subscribe({
      next: (rulesData: RulesConfig) => {
        this.rules.set(rulesData);
        this.loading.set(false);
      },
      error: (error: unknown) => {
        const errorMessage = error instanceof Error ? error.message : 'Failed to load rules';
        this.error.set(errorMessage);
        this.loading.set(false);
      },
    });
  }

  toggleRule(key: keyof RulesConfig): void {
    const currentRules = this.rules();
    const updatedRules: RulesConfig = {
      ...currentRules,
      [key]: !currentRules[key],
    };

    this.rules.set(updatedRules);
    this.updateRules(updatedRules);
  }

  private updateRules(rules: RulesConfig): void {
    this.loading.set(true);
    this.error.set('');

    this.rulesApi.updateRules(rules).subscribe({
      next: (updatedRules: RulesConfig) => {
        this.rules.set(updatedRules);
        this.loading.set(false);
      },
      error: (error: unknown) => {
        const errorMessage = error instanceof Error ? error.message : 'Failed to update rules';
        this.error.set(errorMessage);
        this.loading.set(false);
      },
    });
  }
}
import { CommonModule } from '@angular/common';
import { Component, inject, output, OnInit, effect, signal } from '@angular/core';
import { RulesStore } from '../store/rules.store';
import { ChatStore } from '../../chat/store/chat.store';
import {
  getEnabledSearchProviders,
  getEnabledExtractionMethods,
  hasSearchProviderEnabled,
  hasExtractionEnabled,
} from '../service/rules.model';

@Component({
  selector: 'app-rules-panel',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './rules.page.html',
  styleUrls: ['./rules.page.css'],
})
export class RulesPanelComponent implements OnInit {
  close = output<void>();
  rulesStore = inject(RulesStore);
  chatStore = inject(ChatStore);
  private lastSessionId = signal<string | null>(null);

  // Helper computed signals for UI
  enabledSearchProviders = signal<string[]>([]);
  enabledExtractionMethods = signal<string[]>([]);
  hasSearchEnabled = signal<boolean>(true);
  hasExtractionEnabled = signal<boolean>(true);

  constructor() {
    // Watch for session changes and update rules accordingly
    effect(() => {
      const currentSessionId = this.chatStore.currentSessionId();
      const lastId = this.lastSessionId();

      // Only update if session actually changed
      if (currentSessionId && currentSessionId !== lastId) {
        this.lastSessionId.set(currentSessionId);
        this.rulesStore.setCurrentSession(currentSessionId);
      }
    });

    // Watch for rules changes and update helper signals
    effect(() => {
      const rules = this.rulesStore.rules();
      if (rules) {
        this.enabledSearchProviders.set(getEnabledSearchProviders(rules));
        this.enabledExtractionMethods.set(getEnabledExtractionMethods(rules));
        this.hasSearchEnabled.set(hasSearchProviderEnabled(rules));
        this.hasExtractionEnabled.set(hasExtractionEnabled(rules));
      }
    });
  }

  ngOnInit(): void {
    // Initial sync in case session is already set
    const currentSessionId = this.chatStore.currentSessionId();
    if (currentSessionId) {
      this.lastSessionId.set(currentSessionId);
      this.rulesStore.setCurrentSession(currentSessionId);
    }
  }

  onClose(): void {
    this.close.emit();
  }

  toggleSessionRule(
    key:
      | 'searxng'
      | 'duckduckgo'
      | 'tavily'
      | 'serper'
      | 'tavilyExtract'
      | 'localExtract'
      | 'advanceSearch'
      | 'advanceExtract',
  ): void {
    this.rulesStore.toggleSessionRule(key);
  }

  updateLimit(key: string, event: Event): void {
    const input = event.target as HTMLInputElement;
    const value = input.value;

    if (!value) {
      // Clear the limit if empty
      this.rulesStore.updateLimit(key as any, undefined);
    } else {
      const numValue = parseInt(value, 10);
      if (!isNaN(numValue) && numValue > 0) {
        // Validate ranges
        if (key === 'webSearchLimit' && numValue > 50) {
          input.value = '50';
          this.rulesStore.updateLimit(key as any, 50);
        } else if (key === 'memorySearchLimit' && numValue > 50) {
          input.value = '50';
          this.rulesStore.updateLimit(key as any, 50);
        } else if (key === 'historyLimit' && numValue > 50) {
          input.value = '50';
          this.rulesStore.updateLimit(key as any, 50);
        } else if (key === 'fileUploadMaxChars' && numValue > 500000) {
          input.value = '500000';
          this.rulesStore.updateLimit(key as any, 500000);
        } else {
          this.rulesStore.updateLimit(key as any, numValue);
        }
      }
    }
  }

  updateCustomInstructions(event: Event): void {
    const textarea = event.target as HTMLTextAreaElement;
    const value = textarea.value.trim();

    if (!value) {
      this.rulesStore.updateCustomInstructions('');
    } else {
      // Max 5000 characters
      const truncated = value.substring(0, 5000);
      if (truncated !== value) {
        textarea.value = truncated;
      }
      this.rulesStore.updateCustomInstructions(truncated);
    }
  }

  // Reset to defaults
  resetToDefaults(): void {
    if (confirm('Reset all rules to default values?')) {
      this.rulesStore.resetToDefaults();
    }
  }
}

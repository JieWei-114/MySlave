import { CommonModule } from '@angular/common';
import { Component, inject, output, OnInit, effect, signal } from '@angular/core';
import { RulesStore } from '../store/rules.store';
import { ChatStore } from '../../chat/store/chat.store';

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
      if (!isNaN(numValue)) {
        this.rulesStore.updateLimit(key as any, numValue);
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
      this.rulesStore.updateCustomInstructions(truncated);
    }
  }
}

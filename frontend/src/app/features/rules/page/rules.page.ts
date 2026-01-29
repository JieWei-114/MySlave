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
    key: 'searxng' | 'duckduckgo' | 'tavily' | 'serper' | 'tavilyExtract' | 'localExtract',
  ): void {
    this.rulesStore.toggleSessionRule(key);
  }
}

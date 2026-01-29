import { CommonModule } from '@angular/common';
import { Component, inject, output } from '@angular/core';
import { RulesStore } from '../store/rules.store';

@Component({
  selector: 'app-rules-panel',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './rules.page.html',
  styleUrls: ['./rules.page.css'],
})
export class RulesPanelComponent {
  close = output<void>();
  store = inject(RulesStore);

  onClose(): void {
    this.close.emit();
  }

  toggleRule(
    key: 'searxng' | 'duckduckgo' | 'tavily' | 'serper' | 'tavilyExtract' | 'localExtract',
  ): void {
    this.store.toggleRule(key);
  }
}
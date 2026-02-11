import { Component, input, output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MessageMetadata } from '../../../features/chat/services/chat.model';

@Component({
  selector: 'app-context-indicator',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './context-indicator.component.html',
  styleUrl: './context-indicator.component.css',
})
export class ContextIndicatorComponent {
  // Inputs
  visible = input<boolean>(true);
  metadata = input<MessageMetadata | null>(null);

  // Outputs
  visibleChange = output<boolean>();

  // Section collapse states
  expandedSections = new Map<string, boolean>([
    ['sources', true],
    ['reasoning', true],
    ['veto', true],
    ['guard', true],
    ['uncertainties', true],
    ['confidence', true],
    ['conflicts', false],
  ]);

  onClose() {
    this.visibleChange.emit(false);
  }

  toggleSection(section: string) {
    const current = this.expandedSections.get(section) ?? true;
    this.expandedSections.set(section, !current);
  }

  isSectionExpanded(section: string): boolean {
    return this.expandedSections.get(section) ?? true;
  }

  formatSource(source: string | undefined): string {
    if (!source) return 'Unknown';
    return source.replace('-', ' ').replace(/\b\w/g, (l) => l.toUpperCase());
  }

  getSourcesArray(
    sources: Record<string, number> | undefined,
  ): { source: string; score: number }[] {
    if (!sources) return [];
    return Object.entries(sources).map(([source, score]) => ({ source, score }));
  }

  getRiskLevel(risk: string | undefined): string {
    if (!risk) return 'NONE';
    return risk.toUpperCase();
  }

  getRiskClass(risk: string | undefined): string {
    const level = risk?.toUpperCase() || 'NONE';
    if (level === 'HIGH') return 'high';
    if (level === 'MED') return 'medium';
    if (level === 'LOW') return 'low';
    return 'none';
  }

  getVetoLevel(level: string | undefined): string {
    if (!level) return 'NONE';
    return level.toUpperCase();
  }

  getVetoClass(level: string | undefined): string {
    const l = level?.toLowerCase() || 'none';
    if (l === 'hard') return 'hard';
    if (l === 'soft') return 'soft';
    return 'none';
  }

  /**
   * Build loaded_sources from existing sources_used and sources_considered
   * Infers availability from the data already in the database
   * Uses existing meta.sources_used and meta.sources_considered (no new backend changes needed)
   */
  buildLoadedSources(meta?: any): any {
    const m = meta || this.metadata();
    if (!m) return null;

    // If already built by backend, use it
    if (m.loaded_sources) {
      return m.loaded_sources;
    }

    // Otherwise, derive from sources_used and sources_considered (use existing DB fields)
    const sourcesUsed = m.sources_used || [];
    const sourcesConsidered = m.sources_considered || {};

    return {
      file: {
        available: sourcesUsed.includes('file') || 'file' in sourcesConsidered,
        count: sourcesUsed.includes('file') ? 1 : 0,
      },
      memory: {
        available: sourcesUsed.includes('memory') || 'memory' in sourcesConsidered,
        count: sourcesUsed.includes('memory') ? 1 : 0,
      },
      web: {
        available: sourcesUsed.includes('web') || 'web' in sourcesConsidered,
        count: sourcesUsed.includes('web') ? 1 : 0,
      },
      history: {
        available: sourcesUsed.includes('history') || 'history' in sourcesConsidered,
      },
    };
  }

  formatConfidenceValue(value: number | undefined): string {
    if (value === undefined) return 'N/A';
    return `${(value * 100).toFixed(0)}%`;
  }

  formatAction(action: string): string {
    if (!action) return 'Unknown';
    const formatted = action.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
    const actionMap: Record<string, string> = {
      'Search Web': 'Search the web for more information',
      'Ask User': 'Ask the user for clarification',
      'Use History': 'Refer to conversation history',
      'Verify Source': 'Verify against reliable sources',
    };
    return actionMap[formatted] || formatted;
  }
}

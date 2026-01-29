import {
  Component,
  Input,
  Output,
  EventEmitter,
  AfterViewInit,
  ElementRef,
  Inject,
  PLATFORM_ID,
} from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { CommonModule } from '@angular/common';
import { MemoryPage } from '../../../features/memory/page/memory.page';
import { WebSearchComponent } from '../../../features/web/page/web-search.component';
import { RulesPanelComponent } from '../../../features/rules/page/rules.page';

type PanelTab = 'memory' | 'web' | 'rules';

@Component({
  selector: 'app-panel',
  standalone: true,
  imports: [CommonModule, MemoryPage, WebSearchComponent, RulesPanelComponent],
  templateUrl: './panel.component.html',
  styleUrls: ['./panel.component.css'],
})
export class PanelComponent implements AfterViewInit {
  @Input() sessionId!: string;
  @Output() close = new EventEmitter<void>();

  activeTab: PanelTab = 'memory';
  private isResizing = false;
  private startX = 0;
  private startWidth = 0;

  constructor(
    private elementRef: ElementRef,
    @Inject(PLATFORM_ID) private platformId: Object,
  ) {}

  ngAfterViewInit(): void {
    if (isPlatformBrowser(this.platformId)) {
      this.setupPanelResize();
    }
  }

  private setupPanelResize(): void {
    document.addEventListener('mousedown', (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (!target.classList.contains('panel-resize-handle')) return;

      e.preventDefault();
      this.isResizing = true;
      this.startX = e.clientX;

      const panel = this.elementRef.nativeElement;
      if (!panel) return;

      this.startWidth = panel.offsetWidth;
      document.body.style.cursor = 'ew-resize';
      document.body.style.userSelect = 'none';
    });

    document.addEventListener('mousemove', (e: MouseEvent) => {
      if (!this.isResizing) return;

      e.preventDefault();
      const panel = this.elementRef.nativeElement;
      if (!panel) return;

      const delta = this.startX - e.clientX; // drag left
      const newWidth = this.startWidth + delta;

      if (newWidth >= 390 && newWidth <= 600) {
        panel.style.width = newWidth + 'px';
        panel.style.minWidth = newWidth + 'px';
      }
    });

    document.addEventListener('mouseup', () => {
      if (this.isResizing) {
        this.isResizing = false;
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
      }
    });
  }

  selectTab(tab: PanelTab): void {
    this.activeTab = tab;
  }

  onClose(): void {
    this.close.emit();
  }
}

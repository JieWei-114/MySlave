import {
  Component,
  HostListener,
  ElementRef,
  ViewChild,
  AfterViewInit,
  Inject,
  PLATFORM_ID,
} from '@angular/core';
import { Router, RouterOutlet } from '@angular/router';
import { isPlatformBrowser } from '@angular/common';
import { SidebarComponent } from '../shared/ui/sidebar/sidebar.component';
import { ChatStore } from '../features/chat/store/chat.store';
import { MemoryPage } from '../features/memory/page/memory.page';
import { WebSearchComponent } from '../features/tools/page/web/web-search.component';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, SidebarComponent, MemoryPage, CommonModule, WebSearchComponent],
  templateUrl: './app.shell.html',
  styleUrls: ['./app.shell.css'],
})
export class AppShell implements AfterViewInit {
  showMemory = false;
  sidebarCollapsed = false;
  showWeb = false;
  private isResizing = false;
  private startX = 0;
  private startWidth = 0;

  constructor(
    public store: ChatStore,
    private router: Router,
    private elementRef: ElementRef,
    @Inject(PLATFORM_ID) private platformId: Object,
  ) {
    this.store.loadSessions();
  }

  ngAfterViewInit() {
    if (isPlatformBrowser(this.platformId)) {
      this.setupMemoryResize();
    }
  }

  private setupMemoryResize() {
    document.addEventListener('mousedown', (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (!target.classList.contains('resize-handle')) return;

      e.preventDefault();
      this.isResizing = true;
      this.startX = e.clientX;

      const memoryDrawer = this.elementRef.nativeElement.querySelector('.memory-drawer');
      if (!memoryDrawer) return;

      this.startWidth = memoryDrawer.offsetWidth;
      document.body.style.cursor = 'ew-resize';
      document.body.style.userSelect = 'none';
    });

    document.addEventListener('mousemove', (e: MouseEvent) => {
      if (!this.isResizing) return;

      e.preventDefault();
      const memoryDrawer = this.elementRef.nativeElement.querySelector('.memory-drawer');
      if (!memoryDrawer) return;

      const delta = this.startX - e.clientX; // drag left
      const newWidth = this.startWidth + delta;

      if (newWidth >= 320 && newWidth <= 650) {
        memoryDrawer.style.width = newWidth + 'px';
        memoryDrawer.style.minWidth = newWidth + 'px';
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

  onNewChat(): void {
    this.store.createTempSession();
    this.router.navigate(['/chat', this.store.currentSessionId()]);
  }

  onSelectChat(id: string): void {
    this.store.selectSession(id);
    this.router.navigate(['/chat', id]);
  }
  onDeleteChat(id: string): void {
    this.store.deleteSession(id);

    const next = this.store.sessionIds().find((x) => x !== id);
    if (next) {
      this.router.navigate(['/chat', next]);
    }
  }
  onRenameChat({ id, title }: { id: string; title: string }) {
    this.store.renameSession(id, title);
  }
  toggleMemory() {
    this.showMemory = !this.showMemory;
  }
  toggleSidebar() {
    this.sidebarCollapsed = !this.sidebarCollapsed;
  }
  toggleWeb() {
    this.showWeb = !this.showWeb;
  }
}

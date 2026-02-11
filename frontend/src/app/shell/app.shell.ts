import { Component, AfterViewInit, Inject, PLATFORM_ID } from '@angular/core';
import { Router, RouterOutlet } from '@angular/router';
import { isPlatformBrowser } from '@angular/common';
import { SidebarComponent } from '../shared/ui/sidebar/sidebar.component';
import { PanelComponent } from '../shared/ui/panel/panel.component';
import { ChatStore } from '../features/chat/store/chat.store';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, SidebarComponent, PanelComponent, CommonModule],
  templateUrl: './app.shell.html',
  styleUrls: ['./app.shell.css'],
})
export class AppShell implements AfterViewInit {
  showTools = false;
  sidebarCollapsed = false;

  constructor(
    public store: ChatStore,
    private router: Router,
    @Inject(PLATFORM_ID) private platformId: object,
  ) {
    this.store.loadSessions();
  }

  ngAfterViewInit() {
    if (isPlatformBrowser(this.platformId)) {
      // Panel resize logic is in PanelComponent
    }
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

  onSessionsReordered(sessions: any[]): void {
    this.store.reorderSessions(sessions);
  }

  toggleTools() {
    this.showTools = !this.showTools;
  }
  toggleSidebar() {
    this.sidebarCollapsed = !this.sidebarCollapsed;
  }
}

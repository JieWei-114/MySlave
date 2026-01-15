import { Component } from '@angular/core';
import { Router, RouterOutlet } from '@angular/router';
import { SidebarComponent } from '../shared/ui/sidebar/sidebar.component';
import { ChatStore } from '../features/chat/store/chat.store';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, SidebarComponent],
  templateUrl: './app.shell.html',
  styleUrls: ['./app.shell.css'],
})
export class AppShell {
  constructor(
    public store: ChatStore,
    private router: Router
  ) {
    this.store.loadSessions();
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

    const next = this.store.sessionIds().find(x => x !== id);
    if (next) {
      this.router.navigate(['/chat', next]);
    }
  }
  onRenameChat({ id, title }: { id: string; title: string }) {
  this.store.renameSession(id, title);
  }
}

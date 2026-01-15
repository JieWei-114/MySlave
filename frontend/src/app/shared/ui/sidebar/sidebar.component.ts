import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ChatSession } from '../../../features/chat/services/chat-session.model';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.css']
})
export class SidebarComponent {
  @Input({ required: true }) sessions!: ChatSession[];
  @Input({ required: true }) activeId!: string | null;

  @Output() newSession = new EventEmitter<void>();
  @Output() selectSession = new EventEmitter<string>();
  @Output() deleteSession = new EventEmitter<string>();
  @Output() renameSession = new EventEmitter<{ id: string; title: string }>();

  editingId: string | null = null;
  draftTitle = '';
  
  startEdit(session: ChatSession): void {
    this.editingId = session.id;
    this.draftTitle = session.title;
  }

  commitEdit(): void {
    if (!this.editingId) return;

    this.renameSession.emit({
      id: this.editingId,
      title: this.draftTitle.trim() || 'New chat'
    });
    this.editingId = null;
  }
}

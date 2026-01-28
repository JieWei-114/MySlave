import { Component, EventEmitter, Input, Output, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ChatSession } from '../../../features/chat/services/chat.model';
import { DragDropModule, CdkDragDrop, moveItemInArray } from '@angular/cdk/drag-drop';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, FormsModule, DragDropModule],
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.css'],
})
export class SidebarComponent {
  @Input({ required: true }) sessions!: ChatSession[];
  @Input({ required: true }) activeId!: string | null;
  @Input() collapsed = false;
  @Input() showTools = false;

  @Output() toggleTools = new EventEmitter<void>();
  @Output() toggleSidebar = new EventEmitter<void>();

  @Output() newSession = new EventEmitter<void>();
  @Output() selectSession = new EventEmitter<string>();
  @Output() deleteSession = new EventEmitter<string>();
  @Output() renameSession = new EventEmitter<{ id: string; title: string }>();

  @Output() sessionsReordered = new EventEmitter<ChatSession[]>();

  editingId: string | null = null;
  menuOpenId: string | null = null;
  draftTitle = '';

  startEdit(session: ChatSession): void {
    this.editingId = session.id;
    this.draftTitle = session.title;
    this.menuOpenId = null;
  }

  commitEdit(): void {
    if (!this.editingId) return;

    this.renameSession.emit({
      id: this.editingId,
      title: this.draftTitle.trim() || 'New chat',
    });
    this.editingId = null;
  }

  onDrop(event: CdkDragDrop<ChatSession[]>) {
    moveItemInArray(this.sessions, event.previousIndex, event.currentIndex);
    this.sessionsReordered.emit(this.sessions);
  }

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent) {
    const target = event.target as HTMLElement;
    const isClickInside = target.closest('.menu-container');

    if (!isClickInside) {
      this.menuOpenId = null;
    }
  }

  toggleMenu(id: string, event: Event) {
    event.stopPropagation();
    this.menuOpenId = this.menuOpenId === id ? null : id;
  }
}
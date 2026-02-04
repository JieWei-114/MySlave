import { Component, Input, Output, EventEmitter, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { ChatMessage } from '../../../features/chat/services/chat.model';
import { ChatStore } from '../../../features/chat/store/chat.store';
import { AutoResizeTextareaDirective } from '../../directives/auto-resize-textarea.directive';

@Component({
  selector: 'app-chat-message-bubble',
  standalone: true,
  imports: [CommonModule, FormsModule, AutoResizeTextareaDirective],
  templateUrl: './chat-message-buble.component.html',
  styleUrls: ['./chat-message-buble.component.css'],
})
export class ChatMessageBubbleComponent {
  @Input() message!: ChatMessage;
  @Input() isLastUserMessage = false;

  @Output() editAndResend = new EventEmitter<{
    content: string;
    attachment?: { filename: string; content: string };
  }>();

  /** UI State */
  isEditing = false;
  editedContent = '';
  showReasoning = false;

  constructor(private store: ChatStore) {}

  /** =====================
   *  UI Actions
   *  ===================== */
  toggleReasoning(): void {
    this.showReasoning = !this.showReasoning;
  }

  remember(): void {
    if (!this.message || this.message.remembered) return;

    this.store.rememberMessage(this.message);
  }

  startEdit(): void {
    this.isEditing = true;
    this.editedContent = this.message.content ?? '';
  }

  cancelEdit(): void {
    this.isEditing = false;
    this.editedContent = '';
  }

  saveAndResend(): void {
    const trimmed = this.editedContent.trim();
    if (!trimmed) return;

    this.isEditing = false;
    this.editAndResend.emit({
      content: trimmed,
      attachment: this.message.attachment,
    });
  }

  onEnterKey(event: Event): void {
    const keyboardEvent = event as KeyboardEvent;

    if (keyboardEvent.ctrlKey) {
      keyboardEvent.preventDefault();
      this.saveAndResend();
    }
  }

  /** =====================
   *  Template Helpers
   *  ===================== */
  get isUser(): boolean {
    return this.message?.role === 'user';
  }

  get isAssistant(): boolean {
    return this.message?.role === 'assistant';
  }
}

import { Component, Input, Output, EventEmitter, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { ChatMessage } from '../../../features/chat/services/chat.model';
import { ChatStore } from '../../../features/chat/store/chat.store';
import { AutoResizeTextareaDirective } from '../../directives/auto-resize-textarea.directive';
import { ContextIndicatorComponent } from '../context-indicator/context-indicator.component';

@Component({
  selector: 'app-chat-message-bubble',
  standalone: true,
  imports: [CommonModule, FormsModule, AutoResizeTextareaDirective, ContextIndicatorComponent],
  templateUrl: './chat-message-buble.component.html',
  styleUrls: ['./chat-message-buble.component.css'],
})
export class ChatMessageBubbleComponent implements OnChanges {
  private static reasoningStateByMessage = new Map<string, boolean>();
  private static metadataStateByMessage = new Map<string, boolean>();
  @Input() message!: ChatMessage;
  @Input() isLastUserMessage = false;

  @Output() editAndResend = new EventEmitter<{
    content: string;
    attachment?: { filename: string; content: string };
  }>();

  /**
   * UI State
   */
  isEditing = false;
  editedContent = '';
  showReasoning = false;
  showMetadata = false;
  manuallyToggled = false; // Track if user manually toggled reasoning
  private previousReasoningLength = 0;
  private messageKey = '';

  constructor(private store: ChatStore) {}

  ngOnChanges(changes: SimpleChanges): void {
    if (!changes['message']) return;

    const nextKey = this.message ? `${this.message.role}|${this.message.created_at}` : '';

    if (nextKey && nextKey !== this.messageKey) {
      // Reset per-message UI state when a different message is bound.
      const saved = ChatMessageBubbleComponent.reasoningStateByMessage.get(nextKey);
      this.showReasoning = saved ?? false;
      this.manuallyToggled = saved !== undefined;
      // const savedMetadata = ChatMessageBubbleComponent.metadataStateByMessage.get(nextKey);
      this.showMetadata = false;
      this.previousReasoningLength = 0;
      this.messageKey = nextKey;
    }

    if (this.manuallyToggled) return;

    const currentReasoning = this.message?.meta?.reasoning || '';
    const currentLength = currentReasoning.length;

    // Auto-open only while reasoning is actively streaming and text is growing.
    if (
      this.message?.meta?.reasoning_streaming &&
      currentLength > this.previousReasoningLength &&
      currentLength > 0
    ) {
      this.showReasoning = true;
    }

    this.previousReasoningLength = currentLength;
  }

  /**
   * UI Actions
   */
  toggleReasoning(): void {
    this.showReasoning = !this.showReasoning;
    this.manuallyToggled = true; // Mark as manually toggled to prevent auto-opening
    if (this.messageKey) {
      ChatMessageBubbleComponent.reasoningStateByMessage.set(this.messageKey, this.showReasoning);
    }
  }

  toggleMetadata(): void {
    this.showMetadata = !this.showMetadata;
    if (this.messageKey) {
      ChatMessageBubbleComponent.metadataStateByMessage.set(this.messageKey, this.showMetadata);
    }
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

  /**
   *  Template Helpers
   */
  get isUser(): boolean {
    return this.message?.role === 'user';
  }

  get isAssistant(): boolean {
    return this.message?.role === 'assistant';
  }

  get isReasoningEnabled(): boolean {
    return this.store.reasoningEnabled();
  }
}

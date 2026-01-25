import { Component, Input } from '@angular/core';
import { ChatMessage } from '../../../features/chat/services/chat.model';
import { ChatStore } from '../../../features/chat/store/chat.store';
import { MemoryStore } from '../../../features/memory/store/memory.store';
import { CommonModule } from '@angular/common';
import { MarkdownPipe } from '../../pipes/markdown.pipe';

@Component({
  selector: 'app-chat-message-bubble',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './chat-message-buble.component.html',
  styleUrls: ['./chat-message-buble.component.css'],
})
export class ChatMessageBubbleComponent {
  @Input() message!: ChatMessage;

  constructor(public store: MemoryStore) {}

  remember(): void {
    if (this.message.remembered) return;

    this.store.addManual(this.message.content);
    this.message.remembered = true;
  }

  get isUser(): boolean {
    return this.message.role === 'user';
  }

  get isAssistant(): boolean {
    return this.message.role === 'assistant';
  }
}

import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ChatMessage } from '../../../features/chat/services/chat.model';
import { MarkdownPipe } from '../../pipes/markdown.pipe';

@Component({
  selector: 'app-chat-message-bubble',
  standalone: true,
  imports: [CommonModule, MarkdownPipe],
  template: `
    <div class="bubble" [class.user]="message.role === 'user'">
      <div [innerHTML]="message.content | markdown"></div>
    </div>
  `,
  styles: [`
    .bubble {
      margin-bottom: 6px;
      padding: 6px 8px;
      border-radius: 6px;
      max-width: 70%;
    }
    .bubble.user {
      background: #e0f0ff;
      margin-left: auto;
    }
  `]
})
export class ChatMessageBubbleComponent {
  @Input({ required: true }) message!: ChatMessage;
}

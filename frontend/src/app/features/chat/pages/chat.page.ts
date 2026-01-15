import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';

import { ChatStore } from '../store/chat.store';
import { AppButtonComponent } from '../../../shared/ui/button/app-button.component';
import { ChatMessageBubbleComponent } from '../../../shared/ui/chat-box/chat-message-buble.component';
import { AutoFocusDirective } from '../../../shared/directives/auto-focus.directive';
import { AutoScrollDirective } from '../../../shared/directives/auto-scroll.directive';
import { AutoResizeTextareaDirective } from '../../../shared/directives/auto-resize-textarea.directive';
import { ErrorBannerComponent } from '../../../shared/ui/banner/error-banner.component';
// import { PrefixPipe } from '../../../shared/pipes/prefix.pipe';

@Component({
  selector: 'app-chat-page',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    AppButtonComponent,
    ChatMessageBubbleComponent,
    AutoFocusDirective,
    AutoScrollDirective,
    AutoResizeTextareaDirective,
    ErrorBannerComponent,
    // PrefixPipe
  ],
  templateUrl: './chat.page.html',
  styleUrls: ['./chat.page.css']
})
export class ChatPage {
  message = '';

  constructor(
    public store: ChatStore,
    route: ActivatedRoute
  ) {
    route.paramMap.subscribe(params => {
      const id = params.get('id') ?? 'default';
      this.store.selectSession(id);
    });
  }

  send(): void {
    this.store.sendMessage(this.message);
    this.message = '';
  }

  onKeyDown(event: KeyboardEvent): void {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    this.send();
    }
  }
  get isTyping(): boolean {
  return !!this.message.trim() && !this.store.loading();
  }
  onScroll(e: Event) {
    const el = e.target as HTMLElement;
    if (el.scrollTop < 20) {
      this.store.loadOlderMessages(this.store.currentSessionId()!);
    }
  }
}

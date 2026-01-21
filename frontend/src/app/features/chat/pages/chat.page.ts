import { Component, OnInit, inject, signal, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { HttpClient } from '@angular/common/http';

import { ChatStore } from '../store/chat.store';
import { AVAILABLE_MODELS, AIModel } from '../services/chat.model';
import { AppButtonComponent } from '../../../shared/ui/button/app-button.component';
import { ChatMessageBubbleComponent } from '../../../shared/ui/chat-box/chat-message-buble.component';
import { AutoFocusDirective } from '../../../shared/directives/auto-focus.directive';
import { AutoScrollDirective } from '../../../shared/directives/auto-scroll.directive';
import { ErrorBannerComponent } from '../../../shared/ui/banner/error-banner.component';
import { SkeletonComponent } from '../../../shared/ui/skeleton/skeleton.component';
import { ErrorBoundaryComponent } from '../../../shared/ui/error-boundary/error-boundary.component';
import { AppConfigService } from '../../../core/services/app-config.services';
// import { AutoResizeTextareaDirective } from '../../../shared/directives/auto-resize-textarea.directive';
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
    ErrorBannerComponent,
    SkeletonComponent,
    ErrorBoundaryComponent,
    // AutoResizeTextareaDirective,
    // PrefixPipe
  ],
  templateUrl: './chat.page.html',
  styleUrls: ['./chat.page.css'],
})
export class ChatPage implements OnInit {
  private http = inject(HttpClient);
  private config = inject(AppConfigService);

  message = '';
  models = signal<AIModel[]>(AVAILABLE_MODELS);
  isDropdownOpen = false;
  isErrorDismissed = signal(false);

  constructor(
    public store: ChatStore,
    route: ActivatedRoute,
  ) {
    route.paramMap.subscribe((params) => {
      const id = params.get('id') ?? 'default';
      this.store.selectSession(id);
      this.isErrorDismissed.set(false);
    });
  }

  ngOnInit(): void {
    this.loadModels();
  }

  private loadModels(): void {
    this.http.get<AIModel[]>(`${this.config.apiBaseUrl}/chat/models`).subscribe({
      next: (data) => this.models.set(data),
      error: () => {
        // Fallback to hardcoded models on error
        console.warn('Failed to load models from API, using defaults');
        this.models.set(AVAILABLE_MODELS);
      },
    });
  }

  send(): void {
    this.isErrorDismissed.set(false);
    this.store.sendMessage(this.message);
    this.message = '';
  }

  onModelChange(modelId: string): void {
    const model = this.models().find((m) => m.id === modelId);
    if (model) {
      this.store.setModel(model);
    }
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

  retryLoadSessions(): void {
    this.isErrorDismissed.set(false);
    this.store.loadSessions();
  }

  toggleDropdown(event: MouseEvent) {
    event.stopPropagation();
    this.isDropdownOpen = !this.isDropdownOpen;
  }

  selectModel(model: any) {
    this.onModelChange(model.id);
    this.isDropdownOpen = false;
  }

  @HostListener('document:click')
  onClickOutside() {
    this.isDropdownOpen = false;
  }

  dismissError() {
    this.isErrorDismissed.set(true);
  }
}

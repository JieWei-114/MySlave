import {
  Component,
  OnInit,
  inject,
  signal,
  HostListener,
  ViewChild,
  ElementRef,
  AfterViewInit,
  effect,
  PLATFORM_ID,
} from '@angular/core';
import { isPlatformBrowser, CommonModule } from '@angular/common';
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
import { AutoResizeTextareaDirective } from '../../../shared/directives/auto-resize-textarea.directive';
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
    AutoResizeTextareaDirective,
    // PrefixPipe
  ],
  templateUrl: './chat.page.html',
  styleUrls: ['./chat.page.css'],
})
export class ChatPage implements OnInit, AfterViewInit {
  private http = inject(HttpClient);
  private config = inject(AppConfigService);
  private platformId = inject(PLATFORM_ID);

  @ViewChild('chatTextarea', { read: ElementRef }) textareaRef?: ElementRef<HTMLTextAreaElement>;

  models = signal<AIModel[]>(AVAILABLE_MODELS);
  isDropdownOpen = false;
  isErrorDismissed = signal(false);
  selectedFileName = signal('');
  fileError = signal('');
  private fileContent = signal('');

  get message(): string {
    return this.store.draftMessage();
  }

  set message(value: string) {
    this.store.setDraftMessage(value);
  }

  constructor(
    public store: ChatStore,
    route: ActivatedRoute,
  ) {
    route.paramMap.subscribe((params) => {
      const id = params.get('id') ?? 'default';
      this.store.selectSession(id);
      this.isErrorDismissed.set(false);
    });

    // Watch for draft message changes and auto-resize
    effect(() => {
      this.store.draftMessage();
      this.triggerResize();
    });
  }

  ngOnInit(): void {
    this.loadModels();
  }

  ngAfterViewInit(): void {
    // Lifecycle hook (effect is already in constructor)
  }

  triggerResize(): void {
    // Only run in browser environment
    if (!isPlatformBrowser(this.platformId) || typeof window === 'undefined') return;

    // Trigger resize after programmatic text insertion
    setTimeout(() => {
      const textarea = this.textareaRef?.nativeElement;
      if (textarea) {
        textarea.style.height = 'auto';
        const style = window.getComputedStyle(textarea);
        const maxHeight = parseFloat(style.maxHeight || '0');
        const max = Number.isFinite(maxHeight) && maxHeight > 0 ? maxHeight : Infinity;
        const nextHeight = Math.min(textarea.scrollHeight, max);
        textarea.style.height = `${nextHeight}px`;
        textarea.style.overflowY = textarea.scrollHeight > max ? 'auto' : 'hidden';
      }
    });
  }

  private loadModels(): void {
    this.http.get<AIModel[]>(`${this.config.apiBaseUrl}/chat/models`).subscribe({
      next: (data) => this.models.set(data),
      error: () => {
        console.warn('Failed to load models from API, using defaults');
        this.models.set(AVAILABLE_MODELS);
      },
    });
  }

  send(): void {
    this.isErrorDismissed.set(false);
    let content = this.store.draftMessage().trim();

    // Append file content only when sending
    if (this.fileContent()) {
      const header = `\n\n[Attached file: ${this.selectedFileName()}]\n`;
      content = content + header + this.fileContent();
    }

    if (!content) return;

    this.store.sendMessage(content);
    this.store.clearDraft();
    this.selectedFileName.set('');
    this.fileContent.set('');
    this.fileError.set('');
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
    return !!this.store.draftMessage().trim() && !this.store.loading();
  }

  onScroll(e: Event) {
    const el = e.target as HTMLElement;
    if (el.scrollTop < 20) {
      this.store.loadOlderMessages(this.store.currentSessionId()!);
    }
  }

  onFileSelected(event: Event): void {
    this.fileError.set('');
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;

    const maxBytes = 500_000; // 500 KB
    if (file.size > maxBytes) {
      this.fileError.set('File too large. Max 500KB.');
      input.value = '';
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      const raw = String(reader.result ?? '');
      const content = raw.trim();
      if (!content) {
        this.fileError.set('File is empty or unreadable.');
        input.value = '';
        return;
      }

      this.selectedFileName.set(file.name);
      this.fileContent.set(content);
      input.value = '';
    };

    reader.onerror = () => {
      this.fileError.set('Failed to read file.');
      input.value = '';
    };

    reader.readAsText(file);
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

  clearFile(): void {
    this.selectedFileName.set('');
    this.fileContent.set('');
    this.fileError.set('');
  }
}

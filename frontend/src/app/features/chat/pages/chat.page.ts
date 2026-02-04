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

    if (!content) return;

    const attachment = this.fileContent()
      ? { filename: this.selectedFileName(), content: this.fileContent() }
      : undefined;

    this.store.sendMessage(content, attachment);
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

    const maxBytes = this.config.fileUploadMaxBytes;
    if (file.size > maxBytes) {
      this.fileError.set('File too large. Max 10MB.');
      input.value = '';
      return;
    }

    // Check if it's a binary file (PDF, Word)
    const isBinary = this.config.binaryExtensions.some(ext =>
      file.name.toLowerCase().endsWith(ext)
    );

    if (isBinary) {
      // Upload binary file to backend for extraction
      this.uploadFileToBackend(file);
      input.value = '';
    } else {
      // Read text files directly in browser
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
  }

  private uploadFileToBackend(file: File): void {
    const formData = new FormData();
    formData.append('file', file);

    this.fileError.set('Extracting content...');

    this.http
      .post<{
        content: string;
        filename: string;
      }>(`${this.config.apiBaseUrl}/chat/upload`, formData)
      .subscribe({
        next: (response: { content: string; filename: string }) => {
          this.selectedFileName.set(response.filename);
          this.fileContent.set(response.content);
          this.fileError.set('');
        },
        error: (err: any) => {
          this.fileError.set(err.error?.detail || 'Failed to extract file content.');
          this.selectedFileName.set('');
          this.fileContent.set('');
        },
      });
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

  isLastUserMessage(msg: any, index: number): boolean {
    const messages = this.store.messageList();
    if (msg.role !== 'user') return false;

    // Find the last user message index
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].role === 'user') {
        return i === index;
      }
    }
    return false;
  }

  onEditAndResend(editedContent: string, attachment?: { filename: string; content: string }): void {
    if (!editedContent.trim() || this.store.loading()) return;

    // Remove the last user message and any assistant responses after it
    const messages = this.store.messageList();
    let lastUserIndex = -1;

    // Find last user message
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].role === 'user') {
        lastUserIndex = i;
        break;
      }
    }

    if (lastUserIndex !== -1) {
      // Remove messages from last user message onwards
      this.store.removeMessagesFrom(lastUserIndex);
    }

    // Send the edited message with attachment if present
    this.store.sendMessage(editedContent, attachment);
  }
}

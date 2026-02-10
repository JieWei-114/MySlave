/**
 * Chat Page Component
 * Main interface for chatting with AI
 */
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
  isFileUploading = signal(false);
  private fileContent = signal('');
  private pendingFile: File | null = null;

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
    // Watch for route parameter changes (session ID)
    route.paramMap.subscribe((params: any) => {
      const id = params.get('id') ?? 'default';
      this.store.selectSession(id);
      this.isErrorDismissed.set(false);
    });

    // Auto-resize textarea when draft message changes
    effect(() => {
      this.store.draftMessage();
      this.triggerResize();
    });
  }

  ngOnInit(): void {
    // Load available AI models from backend
    this.loadModels();
  }

  ngAfterViewInit(): void {
    // Lifecycle hook - resize effect is in constructor
  }

  /**
   * Programmatically trigger textarea auto-resize
   * Called when content is inserted programmatically
   */
  triggerResize(): void {
    // Only run in browser environment
    if (!isPlatformBrowser(this.platformId) || typeof window === 'undefined') return;

    // Defer to next tick to ensure DOM is updated
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

  /**
   * Load available AI models from backend API
   * Falls back to default models if API fails
   */
  private loadModels(): void {
    this.http.get<AIModel[]>(`${this.config.apiBaseUrl}/chat/models`).subscribe({
      next: (data: any) => this.models.set(data),
      error: () => {
        console.warn('Failed to load models from API, using defaults');
        this.models.set(AVAILABLE_MODELS);
      },
    });
  }

  /**
   * Send message to AI with optional file attachment
   * Validates content and handles file attachments
   */
  send(): void {
    this.isErrorDismissed.set(false);
    const content = this.store.draftMessage().trim();

    if (!content) return;

    if (this.isFileUploading()) {
      this.fileError.set('Please wait for file extraction to finish.');
      return;
    }

    if (this.pendingFile && !this.fileContent()) {
      this.isFileUploading.set(true);
      this.fileError.set('Extracting content...');
      const fileToUpload = this.pendingFile;
      this.uploadFileToBackend(fileToUpload).subscribe({
        next: (response: { content: string; filename: string }) => {
          this.selectedFileName.set(response.filename);
          this.fileContent.set(response.content);
          this.fileError.set('');
          this.isFileUploading.set(false);
          this.pendingFile = null;
          this.performSend(content);
        },
        error: (err: any) => {
          this.fileError.set(err.error?.detail || 'Failed to extract file content.');
          this.selectedFileName.set('');
          this.fileContent.set('');
          this.isFileUploading.set(false);
          this.pendingFile = null;
        },
      });
      return;
    }

    this.performSend(content);
  }

  private performSend(content: string): void {
    // Attach file content if selected
    const attachment = this.fileContent()
      ? { filename: this.selectedFileName(), content: this.fileContent() }
      : undefined;

    this.store.sendMessage(content, attachment);

    // Clear draft and file selection
    this.store.clearDraft();
    this.selectedFileName.set('');
    this.fileContent.set('');
    this.fileError.set('');
    this.pendingFile = null;
  }

  /**
   * Handle AI model selection change
   */
  onModelChange(modelId: string): void {
    const model = this.models().find((m: any) => m.id === modelId);
    if (model) {
      this.store.setModel(model);
    }
  }

  /**
   * Handle Enter key in textarea
   * Enter = send, Shift+Enter = new line
   */
  onKeyDown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.send();
    }
  }

  /**
   * Check if user is currently typing (for UI feedback)
   */
  get isTyping(): boolean {
    return !!this.store.draftMessage().trim() && !this.store.loading();
  }

  /**
   * Handle scroll event for infinite loading
   * Load older messages when user scrolls to top
   */
  onScroll(e: Event) {
    const el = e.target as HTMLElement;
    if (el.scrollTop < 20) {
      this.store.loadOlderMessages(this.store.currentSessionId()!);
    }
  }

  /**
   * Handle file selection from input
   * Supports both text files (read in browser) and binary files (uploaded to backend)
   */
  onFileSelected(event: Event): void {
    this.fileError.set('');
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;

    // Validate file size
    const maxBytes = this.config.fileUploadMaxBytes;
    if (file.size > maxBytes) {
      this.fileError.set('File too large. Max 10MB.');
      input.value = '';
      return;
    }

    // Check if binary file (requires server-side extraction)
    const isBinary = this.config.binaryExtensions.some((ext: any) =>
      file.name.toLowerCase().endsWith(ext),
    );

    this.isFileUploading.set(true);

    if (isBinary) {
      // Defer binary file upload until Send
      this.pendingFile = file;
      this.selectedFileName.set(file.name);
      this.fileContent.set('');
      this.fileError.set('File ready. Click Send to upload and include it.');
      this.isFileUploading.set(false);
      input.value = '';
    } else {
      // Read text files directly in browser
      const reader = new FileReader();
      reader.onload = () => {
        const raw = String(reader.result ?? '');
        const content = raw.trim();
        if (!content) {
          this.fileError.set('File is empty or unreadable.');
          this.isFileUploading.set(false);
          input.value = '';
          return;
        }

        this.selectedFileName.set(file.name);
        this.fileContent.set(content);
        this.isFileUploading.set(false);
        input.value = '';
      };

      reader.onerror = () => {
        this.fileError.set('Failed to read file.');
        this.isFileUploading.set(false);
        input.value = '';
      };

      reader.readAsText(file);
    }
  }

  /**
   * Upload binary file to backend for text extraction
   * Backend handles PDF, Word, and other complex formats
   */
  private uploadFileToBackend(file: File) {
    const formData = new FormData();
    formData.append('file', file);

    return this.http.post<{
      content: string;
      filename: string;
    }>(`${this.config.apiBaseUrl}/chat/upload`, formData);
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
    this.isFileUploading.set(false);
    this.pendingFile = null;
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
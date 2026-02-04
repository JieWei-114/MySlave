import {
  Directive,
  ElementRef,
  HostListener,
  AfterViewInit,
  Inject,
  PLATFORM_ID,
} from '@angular/core';
import { isPlatformBrowser } from '@angular/common';

@Directive({
  selector: 'textarea[appAutoResize]',
  standalone: true,
})
export class AutoResizeTextareaDirective implements AfterViewInit {
  constructor(
    private el: ElementRef<HTMLTextAreaElement>,
    @Inject(PLATFORM_ID) private platformId: any,
  ) {}

  ngAfterViewInit(): void {
    if (!isPlatformBrowser(this.platformId)) return;
    // Resize on initial load to handle pre-filled content
    setTimeout(() => this.resize(), 0);
  }

  @HostListener('input')
  @HostListener('ngModelChange')
  resize(): void {
    if (!isPlatformBrowser(this.platformId)) return;

    const textarea = this.el.nativeElement;
    textarea.style.height = 'auto';
    const style = window.getComputedStyle(textarea);
    const maxHeight = parseFloat(style.maxHeight || '0');
    const max = Number.isFinite(maxHeight) && maxHeight > 0 ? maxHeight : Infinity;
    const nextHeight = Math.min(textarea.scrollHeight, max);

    textarea.style.height = `${nextHeight}px`;
    textarea.style.overflowY = textarea.scrollHeight > max ? 'auto' : 'hidden';
  }
}

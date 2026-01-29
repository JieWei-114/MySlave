import { Directive, ElementRef, HostListener } from '@angular/core';

@Directive({
  selector: 'textarea[appAutoResize]',
  standalone: true,
})
export class AutoResizeTextareaDirective {
  constructor(private el: ElementRef<HTMLTextAreaElement>) {}

  @HostListener('input')
  resize(): void {
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

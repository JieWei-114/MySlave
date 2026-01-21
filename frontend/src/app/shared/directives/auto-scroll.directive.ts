import { Directive, ElementRef, OnDestroy, OnInit, Inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';

@Directive({
  selector: '[appAutoScroll]',
})
export class AutoScrollDirective implements OnInit, OnDestroy {
  private mo: MutationObserver | null = null;

  constructor(
    private el: ElementRef<HTMLElement>,
    @Inject(PLATFORM_ID) private platformId: any,
  ) {}

  ngOnInit(): void {
    if (!isPlatformBrowser(this.platformId)) return;

    this.mo = new MutationObserver(() => this.scrollToBottom());
    this.mo.observe(this.el.nativeElement, { childList: true, subtree: true });

    // initial scroll
    setTimeout(() => this.scrollToBottom(), 0);
  }

  private scrollToBottom(): void {
    try {
      const host = this.el.nativeElement;
      host.scrollTop = host.scrollHeight;
    } catch {}
  }

  ngOnDestroy(): void {
    this.mo?.disconnect();
    this.mo = null;
  }
}

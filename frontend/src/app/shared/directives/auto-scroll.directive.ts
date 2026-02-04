import { Directive, ElementRef, OnDestroy, OnInit, Inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';

@Directive({
  selector: '[appAutoScroll]',
})
export class AutoScrollDirective implements OnInit, OnDestroy {
  private mo: MutationObserver | null = null;
  private wasAtBottom = true;

  constructor(
    private el: ElementRef<HTMLElement>,
    @Inject(PLATFORM_ID) private platformId: any,
  ) {}

  ngOnInit(): void {
    if (!isPlatformBrowser(this.platformId)) return;

    this.mo = new MutationObserver(() => this.handleMutation());
    this.mo.observe(this.el.nativeElement, { childList: true, subtree: true });

    // Track scroll position to know if user has scrolled up
    this.el.nativeElement.addEventListener('scroll', () => this.checkScrollPosition());

    // initial scroll
    setTimeout(() => this.scrollToBottom(), 0);
  }

  private checkScrollPosition(): void {
    const host = this.el.nativeElement;
    const threshold = 100; // pixels from bottom
    this.wasAtBottom = host.scrollHeight - host.scrollTop - host.clientHeight < threshold;
  }

  private handleMutation(): void {
    // Only auto-scroll if user was already at the bottom
    if (this.wasAtBottom) {
      this.scrollToBottom();
    }
  }

  private scrollToBottom(): void {
    try {
      const host = this.el.nativeElement;
      host.scrollTop = host.scrollHeight;
      this.wasAtBottom = true;
    } catch {}
  }

  ngOnDestroy(): void {
    this.mo?.disconnect();
    this.mo = null;
  }
}

import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-error-banner',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="error" *ngIf="message">
      {{ message }}
    </div>
  `,
  styles: [`
    .error {
      background: #ffe0e0;
      color: #900;
      padding: 6px;
      margin-top: 8px;
      border-radius: 4px;
    }
  `]
})
export class ErrorBannerComponent {
  @Input() message = '';
}

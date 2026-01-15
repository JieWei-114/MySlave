import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-button',
  standalone: true,
  imports: [
    CommonModule,
  ],
  template: `
    <button
      class="app-button"
      [disabled]="disabled || loading"
    >
      <span *ngIf="loading" class="spinner"></span>

      <span *ngIf="!loading">
        <ng-content></ng-content>
      </span>
    </button>
  `,
  styles: [`
    .app-button {
      padding: 6px 12px;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      cursor: pointer;
    }

    .app-button:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }

    .spinner {
      width: 14px;
      height: 14px;
      border: 2px solid #ccc;
      border-top-color: #333;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }
  `]
})
export class AppButtonComponent {
  @Input() disabled = false;
  @Input() loading = false;
}

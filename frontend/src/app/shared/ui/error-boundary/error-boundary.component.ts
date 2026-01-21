import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-error-boundary',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './error-boundary.component.html',
  styleUrls: ['./error-boundary.component.css'],
})
export class ErrorBoundaryComponent {
  @Input() error: string | null = null;
  @Input() showRetry = true;
  @Output() retry = new EventEmitter<void>();
  @Output() close = new EventEmitter<void>();
}

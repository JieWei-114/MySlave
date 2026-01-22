import { Component, Input, OnInit, effect, signal, Output, EventEmitter } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { MemoryStore } from '../store/memory.store';
import { AppButtonComponent } from '../../../shared/ui/button/app-button.component';
@Component({
  selector: 'app-memory-panel',
  standalone: true,
  imports: [FormsModule, CommonModule, AppButtonComponent],
  templateUrl: './memory.page.html',
  styleUrls: ['./memory.page.css'],
})
export class MemoryPage {
  private _sessionId = signal<string | null>(null);

  @Input({ required: true })
  set sessionId(value: string) {
    this._sessionId.set(value);
  }

  @Output() close = new EventEmitter<void>();

  newMemory = '';

  constructor(public store: MemoryStore) {
    effect(() => {
      const id = this._sessionId();
      if (!id) return;

      console.log('[Memory] reload for session:', id);
      this.store.load(id);
    });
  }

  add() {
    if (!this.newMemory.trim()) return;
    this.store.addManual(this.newMemory);
    this.newMemory = '';
  }
  
  compress() {
    this.store.compress();
  }
}

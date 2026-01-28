import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { ChatStore } from '../../chat/store/chat.store';
import { WebApi } from '../service/web.api';
import { QuotaInfo, WebSearchResult } from '../service/web.model';
import { AppButtonComponent } from '../../../shared/ui/button/app-button.component';

@Component({
  selector: 'app-web-search',
  standalone: true,
  imports: [FormsModule, CommonModule, AppButtonComponent],
  templateUrl: './web-search.component.html',
  styleUrls: ['./web-search.component.css'],
})
export class WebSearchComponent implements OnInit {
  q = '';
  results: WebSearchResult[] = [];
  quotas: QuotaInfo | null = null;
  loading = false;

  constructor(
    private api: WebApi,
    private chatStore: ChatStore,
  ) {}

  ngOnInit(): void {
    this.loadQuotas();
  }

  loadQuotas(): void {
    this.api.getQuotas().subscribe({
      next: (quotas) => {
        this.quotas = quotas;
      },
      error: () => {
        this.quotas = null;
      },
    });
  }

  search() {
    this.loading = true;
    this.results = [];

    this.api.webSearch(this.q).subscribe({
      next: (res) => {
        this.results = [...(res.results ?? [])];
        this.quotas = res.quotas ?? null;
        this.loading = false;
      },
      error: () => {
        this.loading = false;
      },
    });
  }

  insert(r: any) {
    this.chatStore.appendToDraft(`Web result:\n${r.title}\n${r.snippet}\n${r.link}`);
  }
}
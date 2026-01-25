import { Component, Output, EventEmitter } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { ChatStore } from '../../../chat/store/chat.store';
import { ToolsApi } from '../../service/tools.api';


@Component({
  selector: 'app-web-search',
  standalone: true,
  imports: [FormsModule, CommonModule],
  templateUrl: './web-search.component.html',
  styleUrls: ['./web-search.component.css'],
})
export class WebSearchComponent {
  q = '';
  results: any[] = [];
  quotas  = 0;

  constructor(
    private api: ToolsApi,
    private chatStore: ChatStore,
  ) {}

  @Output() close = new EventEmitter<void>();

  search() {
    this.api.webSearch(this.q).subscribe((res) => {
      this.results = res.results;
      this.quotas = res.quotas;
    });
  }

  insert(r: any) {
    this.chatStore.sendMessage(
      `Web result:\n${r.title}\n${r.snippet}\n${r.link}`
    );
  }
}

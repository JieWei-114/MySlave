import { Component } from '@angular/core';
import { ChatStore } from '../../../chat/store/chat.store';
import { ToolsApi } from '../../service/tools.api';

@Component({
  selector: 'app-web-search',
  standalone: true,
  templateUrl: './web-search.component.html',
  styleUrls: ['./web-search.component.css'],
})
export class WebSearchComponent {
  q = '';
  results: any[] = [];
  remaining = 0;

  constructor(
    private api: ToolsApi,
    private chatStore: ChatStore,
  ) {}

  search() {
    this.api.webSearch(this.q).subscribe((res) => {
      this.results = res.results;
      this.remaining = res.remaining;
    });
  }

  insert(r: any) {
    this.chatStore.sendMessage(
      `Web result:\n${r.title}\n${r.snippet}\n${r.link}`
    );
  }
}

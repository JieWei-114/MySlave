import { ChatMessage } from './chat.model';

export interface ChatSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  hasMore?: boolean;
  loadingMore?: boolean;
}
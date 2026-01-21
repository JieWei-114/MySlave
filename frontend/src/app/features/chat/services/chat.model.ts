export type ChatRole = 'user' | 'assistant';
export interface ChatMessage {
  role: ChatRole;
  content: string;
  created_at: string;

  remembered?: boolean;
}

export interface ChatSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  hasMore?: boolean;
  loadingMore?: boolean;
}

export interface AIModel {
  id: string;
  name: string;
  description?: string;
}

export const AVAILABLE_MODELS: AIModel[] = [
  {
    id: 'gemma3:1b',
    name: 'Gemma 3 (1B)',
    description: 'Fast and efficient',
  },
  {
    id: 'qwen2.5:3b',
    name: 'qwen 2.5 (3B)',
    description: 'Balanced performance',
  },
];

export const DEFAULT_MODEL = AVAILABLE_MODELS[0];

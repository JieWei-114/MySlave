export interface Memory {
  id: string;
  content: string;
  enabled: boolean;
  created_at: string;
  source?: 'manual' | 'auto';
}
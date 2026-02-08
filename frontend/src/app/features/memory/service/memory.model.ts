export interface Memory {
  id: string;
  content: string;
  enabled: boolean;
  created_at: string;
  category?: 'preference_or_fact' | 'important' | 'other';
  source?: 'manual' | 'auto' | 'compress';
}
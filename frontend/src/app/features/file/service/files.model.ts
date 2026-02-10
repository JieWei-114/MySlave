/**
 * File attachment model
 */
export interface FileAttachment {
  id: string;
  session_id: string;
  filename: string;
  file_type: string;
  size_bytes: number;
  size_chars: number;
  uploaded_at: string;
  expires_at?: string | null;
}

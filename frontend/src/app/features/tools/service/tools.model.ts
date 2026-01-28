export interface QuotaInfo {
  serper_remaining: number;
  tavily_remaining: number;
}

export interface WebSearchResult {
  title: string;
  snippet: string;
  link: string;
  source?: string;
}

export interface WebSearchResponse {
  results: WebSearchResult[];
  quotas: QuotaInfo;
}
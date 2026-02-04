export interface RulesConfig {
  searxng: boolean;
  duckduckgo: boolean;
  tavily: boolean;
  serper: boolean;
  tavilyExtract: boolean;
  localExtract: boolean;

  advanceSearch: boolean;
  advanceExtract: boolean;

  webSearchLimit?: number;
  memorySearchLimit?: number;
  historyLimit?: number;
  fileUploadMaxChars?: number;

  customInstructions?: string;
}

export const DEFAULT_RULES: RulesConfig = {
  searxng: true,
  duckduckgo: true,
  tavily: false,
  serper: false,
  tavilyExtract: false,
  localExtract: true,
  advanceSearch: false,
  advanceExtract: false,
  customInstructions: '',
};

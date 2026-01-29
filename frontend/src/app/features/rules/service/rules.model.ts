export interface RulesConfig {
  searxng: boolean;
  duckduckgo: boolean;
  tavily: boolean;
  serper: boolean;
  tavilyExtract: boolean;
  localExtract: boolean;
}

export const DEFAULT_RULES: RulesConfig = {
  searxng: true,
  duckduckgo: true,
  tavily: true,
  serper: true,
  tavilyExtract: true,
  localExtract: true,
};
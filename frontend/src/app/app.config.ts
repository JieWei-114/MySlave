/**
 * Application configuration for the Angular application
 * This file sets up the root-level providers for the entire app
 */
import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideRouter } from '@angular/router';
import { CORE_PROVIDERS } from './core/core.providers';

import { routes } from './app.routes';
import { provideClientHydration, withEventReplay } from '@angular/platform-browser';

export const appConfig: ApplicationConfig = {
  providers: [
    // Global error listeners for better error handling
    provideBrowserGlobalErrorListeners(),
    // Configure application routing
    provideRouter(routes),
    // Enable client-side hydration for SSR with event replay
    provideClientHydration(withEventReplay()),
    // Core providers including HTTP client with interceptors
    ...CORE_PROVIDERS,
  ],
};
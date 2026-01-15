import {
  provideHttpClient,
  withInterceptors,
  withFetch
} from '@angular/common/http';

import { loggingInterceptor } from './interceptors/logging.interceptor';

export const CORE_PROVIDERS = [
  provideHttpClient(
    withFetch(),
    withInterceptors([loggingInterceptor])
  )
];

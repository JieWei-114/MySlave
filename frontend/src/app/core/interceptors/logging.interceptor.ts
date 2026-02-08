import { HttpInterceptorFn } from '@angular/common/http';

export const loggingInterceptor: HttpInterceptorFn = (req, next) => {
  // Log all outgoing HTTP requests
  console.log('[HTTP REQUEST]', req.method, req.url, req.body, req.headers);

  return next(req);
};

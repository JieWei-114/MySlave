import { CanActivateFn } from '@angular/router';

export const authGuard: CanActivateFn = () => {
  const loggedIn = true; // If need replace with real authentication check later
  return loggedIn;
};

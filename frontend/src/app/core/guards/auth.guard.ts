import { CanActivateFn } from '@angular/router';

export const authGuard: CanActivateFn = () => {
  const loggedIn = true; // Replace with real authentication check later
  return loggedIn;
};

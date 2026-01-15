import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  {
    path: '',
    pathMatch: 'full',
    redirectTo: 'chat'
  },
  {
    path: 'chat',
    canActivate: [authGuard],
    loadChildren: () =>
      import('./features/chat/chat.routes').then(m => m.routes)
  },
  {
    path: '**',
    redirectTo: 'chat'
  }
];

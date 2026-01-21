import { Routes } from '@angular/router';
import { ChatPage } from './pages/chat.page';

export const routes: Routes = [
  {
    path: '',
    component: ChatPage,
  },
  {
    path: ':id',
    component: ChatPage,
  },
];

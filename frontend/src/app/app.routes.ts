import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./components/chat/chat.component').then((m) => m.ChatComponent),
    title: 'Chat - CRM Assistant',
  },
  {
    path: 'opportunities',
    loadComponent: () =>
      import('./components/opportunities/opportunities.component').then(
        (m) => m.OpportunitiesComponent
      ),
    title: 'CRM Opportunities',
  },
  {
    path: 'logs',
    loadComponent: () =>
      import('./components/logs/logs.component').then((m) => m.LogsComponent),
    title: 'Interaction Logs',
  },
  {
    path: 'prompts',
    loadComponent: () =>
      import('./components/prompts/prompts.component').then((m) => m.PromptsComponent),
    title: 'System Prompts',
  },
];

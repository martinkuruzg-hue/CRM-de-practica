import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ChatService, InteractionLog } from '../../services/chat.service';

@Component({
  selector: 'app-logs',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './logs.component.html',
  styleUrls: ['./logs.component.css'],
})
export class LogsComponent implements OnInit {
  private chatService = inject(ChatService);
  logs: InteractionLog[] = [];
  loading = true;

  ngOnInit() {
    this.chatService.getLogs().subscribe({
      next: (logs) => {
        this.logs = logs;
        this.loading = false;
      },
      error: () => (this.loading = false),
    });
  }
}

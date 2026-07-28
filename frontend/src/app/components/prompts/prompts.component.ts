import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ChatService, SystemPrompt } from '../../services/chat.service';

@Component({
  selector: 'app-prompts',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './prompts.component.html',
  styleUrls: ['./prompts.component.css'],
})
export class PromptsComponent implements OnInit {
  private chatService = inject(ChatService);
  prompts: SystemPrompt[] = [];
  loading = true;

  ngOnInit() {
    this.chatService.getSystemPrompts().subscribe({
      next: (prompts) => {
        this.prompts = prompts;
        this.loading = false;
      },
      error: () => (this.loading = false),
    });
  }
}

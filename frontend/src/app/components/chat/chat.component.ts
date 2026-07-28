import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ChatService, ChatResponse, SystemPrompt } from '../../services/chat.service';

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.css'],
})
export class ChatComponent implements OnInit {
  private chatService = inject(ChatService);

  messages: { role: string; content: string; tool_name?: string; evaluation?: boolean }[] = [];
  userInput = '';
  loading = false;
  conversationId = '';
  systemPrompts: SystemPrompt[] = [];
  selectedPromptVersion = '';
  showHallucinationInfo = false;
  lastHallucinationCheck: any = null;
  lastTokensUsed = 0;
  lastLatencyMs = 0;

  ngOnInit() {
    this.chatService.getSystemPrompts().subscribe({
      next: (prompts) => {
        this.systemPrompts = prompts;
        const active = prompts.find((p) => p.is_active);
        if (active) this.selectedPromptVersion = active.version;
      },
    });
  }

  sendMessage() {
    if (!this.userInput.trim() || this.loading) return;

    const userMsg = this.userInput;
    this.messages.push({ role: 'user', content: userMsg });
    this.loading = true;
    this.userInput = '';

    this.chatService
      .sendMessage({
        conversation_id: this.conversationId,
        message: userMsg,
        system_prompt_version: this.selectedPromptVersion,
      })
      .subscribe({
        next: (res: ChatResponse) => {
          this.conversationId = res.conversation_id;
          this.messages.push({ role: 'assistant', content: res.assistant_response });
          this.lastHallucinationCheck = res.hallucination_check;
          this.lastTokensUsed = res.tokens_used;
          this.lastLatencyMs = res.latency_ms;

          if (res.tools_used?.length) {
            this.messages[this.messages.length - 1].tool_name = res.tools_used
              .map((t: any) => t.name)
              .join(', ');
          }

          this.loading = false;
        },
        error: () => {
          this.messages.push({
            role: 'assistant',
            content: 'Error connecting to the assistant. Is the server running?',
          });
          this.loading = false;
        },
      });
  }

  evaluate(messageIndex: number, isHelpful: boolean) {
    this.chatService.submitEvaluation({ message_id: '', is_helpful: isHelpful }).subscribe();
    this.messages[messageIndex].evaluation = true;
  }

  newConversation() {
    this.messages = [];
    this.conversationId = '';
    this.lastHallucinationCheck = null;
  }
}

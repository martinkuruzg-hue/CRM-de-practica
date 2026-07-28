import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CrmService, Opportunity } from '../../services/crm.service';

@Component({
  selector: 'app-opportunities',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './opportunities.component.html',
  styleUrls: ['./opportunities.component.css'],
})
export class OpportunitiesComponent implements OnInit {
  private crmService = inject(CrmService);
  opportunities: Opportunity[] = [];
  loading = true;

  ngOnInit() {
    this.crmService.getOpportunities().subscribe({
      next: (data) => {
        this.opportunities = data;
        this.loading = false;
      },
      error: () => (this.loading = false),
    });
  }

  stageClass(stage: string): string {
    const map: Record<string, string> = {
      prospecting: 'stage-prospecting',
      qualification: 'stage-qualification',
      proposal: 'stage-proposal',
      negotiation: 'stage-negotiation',
      closed_won: 'stage-won',
      closed_lost: 'stage-lost',
    };
    return map[stage] || '';
  }

  priorityClass(priority: string): string {
    return `priority-${priority}`;
  }
}

import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
  CrmService,
  Opportunity,
  PipelineStats,
  OpportunityFilters,
  STAGES,
  PRIORITIES,
  CURRENCIES,
} from '../../services/crm.service';

@Component({
  selector: 'app-opportunities',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './opportunities.component.html',
  styleUrls: ['./opportunities.component.css'],
})
export class OpportunitiesComponent implements OnInit {
  private crmService = inject(CrmService);

  opportunities: Opportunity[] = [];
  filtered: Opportunity[] = [];
  loading = true;
  error = '';

  stats: PipelineStats | null = null;

  stages = STAGES;
  priorities = PRIORITIES;
  currencies = CURRENCIES;

  filters: OpportunityFilters = { is_active: true };
  owners: string[] = [];

  // Modal state
  showFormModal = false;
  showDetailModal = false;
  editing = false;
  saving = false;
  form: Partial<Opportunity> = {};
  selected: Opportunity | null = null;

  ngOnInit() {
    this.loadAll();
  }

  loadAll() {
    this.loading = true;
    this.error = '';
    this.crmService.getStats().subscribe({
      next: (s) => (this.stats = s),
      error: () => (this.stats = null),
    });
    this.crmService.getOpportunities(this.filters).subscribe({
      next: (data) => {
        this.opportunities = data;
        this.owners = [...new Set(data.map((o) => o.owner).filter(Boolean))];
        this.applyLocalFilters();
        this.loading = false;
      },
      error: () => {
        this.error = 'No se pudieron cargar las oportunidades. Verifica que el backend esté corriendo.';
        this.loading = false;
      },
    });
  }

  applyLocalFilters() {
    const { search } = this.filters;
    this.filtered = search
      ? this.opportunities.filter(
          (o) =>
            o.company_name.toLowerCase().includes(search.toLowerCase()) ||
            o.contact_name.toLowerCase().includes(search.toLowerCase()) ||
            o.opportunity_name.toLowerCase().includes(search.toLowerCase()) ||
            o.owner.toLowerCase().includes(search.toLowerCase())
        )
      : [...this.opportunities];
  }

  onFilterChange() {
    this.applyLocalFilters();
    this.loadAll();
  }

  resetFilters() {
    this.filters = { is_active: true };
    this.onFilterChange();
  }

  // --- Create / Edit ---
  openCreate() {
    this.editing = false;
    this.form = {
      company_name: '',
      contact_name: '',
      contact_email: '',
      opportunity_name: '',
      description: '',
      estimated_value: 0,
      currency: 'USD',
      stage: 'Lead nuevo',
      priority: 'Media',
      probability: 0,
      owner: '',
      next_follow_up_date: '',
    };
    this.showFormModal = true;
  }

  openEdit(opp: Opportunity) {
    this.editing = true;
    this.form = { ...opp };
    this.showFormModal = true;
  }

  saveOpportunity() {
    if (!this.form.company_name || !this.form.opportunity_name) return;
    this.saving = true;
    const payload = { ...this.form };

    const request = this.editing
      ? this.crmService.updateOpportunity(this.form.id!, payload)
      : this.crmService.createOpportunity(payload);

    request.subscribe({
      next: () => {
        this.saving = false;
        this.showFormModal = false;
        this.loadAll();
      },
      error: () => {
        this.saving = false;
        this.error = 'No se pudo guardar la oportunidad. Revisa los campos.';
      },
    });
  }

  // --- Detail ---
  openDetail(opp: Opportunity) {
    this.selected = opp;
    this.showDetailModal = true;
  }

  closeModals() {
    this.showFormModal = false;
    this.showDetailModal = false;
  }

  // --- Delete (soft) ---
  confirmDelete(opp: Opportunity) {
    if (!confirm(`¿Desactivar la oportunidad "${opp.opportunity_name}" de ${opp.company_name}?`)) return;
    this.crmService.deleteOpportunity(opp.id).subscribe({
      next: () => this.loadAll(),
      error: () => (this.error = 'No se pudo eliminar la oportunidad.'),
    });
  }

  toggleActive(opp: Opportunity) {
    this.crmService
      .updateOpportunity(opp.id, { is_active: !opp.is_active })
      .subscribe({ next: () => this.loadAll() });
  }

  // --- Helpers ---
  stageClass(stage: string): string {
    const map: Record<string, string> = {
      'Lead nuevo': 'stage-new',
      Contactado: 'stage-contactado',
      Diagnóstico: 'stage-diagnostico',
      'Propuesta enviada': 'stage-propuesta',
      Negociación: 'stage-negociacion',
      Ganado: 'stage-ganado',
      Perdido: 'stage-perdido',
    };
    return map[stage] || '';
  }

  priorityClass(priority: string): string {
    const map: Record<string, string> = {
      Baja: 'priority-baja',
      Media: 'priority-media',
      Alta: 'priority-alta',
      'Crítica': 'priority-critica',
    };
    return map[priority] || '';
  }

  formatDate(value: string | null | undefined): string {
    if (!value) return '—';
    const d = new Date(value);
    if (isNaN(d.getTime())) return value;
    return d.toISOString().slice(0, 10);
  }
}

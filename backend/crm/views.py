from datetime import date, timedelta
from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Opportunity
from .serializers import OpportunitySerializer, OpportunitySummarySerializer


class OpportunityViewSet(viewsets.ModelViewSet):
    queryset = Opportunity.objects.all()
    serializer_class = OpportunitySerializer

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params

        is_active = params.get('is_active')
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() in ('true', '1'))

        stage = params.get('stage')
        if stage:
            qs = qs.filter(stage=stage)

        priority = params.get('priority')
        if priority:
            qs = qs.filter(priority=priority)

        owner = params.get('owner')
        if owner:
            qs = qs.filter(owner__icontains=owner)

        search = params.get('search')
        if search:
            qs = qs.filter(
                Q(company_name__icontains=search)
                | Q(contact_name__icontains=search)
                | Q(opportunity_name__icontains=search)
            )

        return qs

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        qs = Opportunity.objects.filter(is_active=True)

        by_stage = {}
        by_priority = {}
        by_owner = {}

        for opp in qs:
            by_stage.setdefault(opp.stage, {'count': 0, 'value': 0.0})
            by_stage[opp.stage]['count'] += 1
            by_stage[opp.stage]['value'] += opp.estimated_value

            by_priority.setdefault(opp.priority, {'count': 0, 'value': 0.0})
            by_priority[opp.priority]['count'] += 1
            by_priority[opp.priority]['value'] += opp.estimated_value

            owner_key = opp.owner or 'Sin asignar'
            by_owner.setdefault(owner_key, {'count': 0, 'value': 0.0})
            by_owner[owner_key]['count'] += 1
            by_owner[owner_key]['value'] += opp.estimated_value

        today = date.today()
        week_end = today + timedelta(days=7)
        follow_up_this_week = qs.filter(
            next_follow_up_date__gte=today,
            next_follow_up_date__lte=week_end,
        ).exclude(stage='Ganado').exclude(stage='Perdido').count()

        won_value = sum(
            opp.estimated_value for opp in qs if opp.stage == 'Ganado'
        )

        data = {
            'total_opportunities': qs.count(),
            'total_pipeline_value': sum(o.estimated_value for o in qs),
            'won_value': won_value,
            'by_stage': by_stage,
            'by_priority': by_priority,
            'by_owner': by_owner,
            'follow_up_this_week': follow_up_this_week,
        }
        return Response(OpportunitySummarySerializer(data).data)

    @action(detail=True, methods=['post'], url_path='ai')
    def ai_interact(self, request, pk=None):
        try:
            opportunity = self.get_object()
        except Opportunity.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        user_message = request.data.get('message', '')
        recommendation = self._generate_ai_recommendation(opportunity, user_message)

        opportunity.ai_recommendation = recommendation
        opportunity.save()

        return Response({
            'opportunity_id': str(opportunity.id),
            'user_message': user_message,
            'ai_response': recommendation,
        })

    def _generate_ai_recommendation(self, opp, user_message):
        base = (
            f"Oportunidad '{opp.opportunity_name}' para {opp.company_name} "
            f"(Etapa: {opp.stage}, Prioridad: {opp.priority}, Valor: {opp.estimated_value:,.0f} {opp.currency}, "
            f"Probabilidad: {opp.probability}%)."
        )

        if user_message:
            action = (
                "priorizar el seguimiento"
                if opp.priority in ('Alta', 'Crítica')
                else "nutrir la relación comercial"
            )
            next_step = (
                "Agendar demo o reunión de propuesta."
                if opp.stage in ('Lead nuevo', 'Contactado', 'Diagnóstico')
                else "Preparar términos finales y cerrar."
                if opp.stage == 'Negociación'
                else "Revisar y optimizar estrategia."
            )
            return (
                f"{base}\n"
                f"Consulta del usuario: {user_message}\n\n"
                f"Sugerencia IA: según la etapa '{opp.stage}' y una probabilidad del {opp.probability}%, "
                f"considere {action}.\n"
                f"Acción recomendada: {next_step}"
            )

        if opp.probability < 30:
            action = "Aumentar engagement con contenido específico."
        elif opp.probability < 60:
            action = "Agendar reunión de seguimiento para resolver inquietudes."
        else:
            action = "Preparar contrato y avanzar al cierre."

        return f"{base}\nRecomendación IA: {action}"

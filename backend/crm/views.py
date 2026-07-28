from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q

from .models import Opportunity
from .serializers import OpportunitySerializer


class OpportunityViewSet(viewsets.ModelViewSet):
    queryset = Opportunity.objects.all()
    serializer_class = OpportunitySerializer

    def get_queryset(self):
        qs = super().get_queryset()
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() in ('true', '1'))
        return qs

    def perform_destroy(self, instance):
        instance.is_active = False
        from datetime import datetime
        instance.updated_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        instance.save()

    @action(detail=False, methods=['delete'], url_path='hard-delete/(?P<pk>[^/]+)')
    def hard_delete(self, request, pk=None):
        try:
            instance = Opportunity.objects.get(pk=pk)
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Opportunity.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'], url_path='ai')
    def ai_interact(self, request, pk=None):
        try:
            opportunity = self.get_object()
        except Opportunity.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        user_message = request.data.get('message', '')

        recommendation = self._generate_ai_recommendation(opportunity, user_message)

        opportunity.ai_recommendation = recommendation
        from datetime import datetime
        opportunity.updated_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        opportunity.save()

        return Response({
            'opportunity_id': opportunity.id,
            'user_message': user_message,
            'ai_response': recommendation,
        })

    def _generate_ai_recommendation(self, opp, user_message):
        value = opp.estimated_value
        stage = opp.stage
        priority = opp.priority
        probability = opp.probability

        base = (
            f"Opportunity '{opp.opportunity_name}' for {opp.company_name} "
            f"(Stage: {stage}, Priority: {priority}, Value: {value} {opp.currency}, "
            f"Probability: {probability}%)."
        )

        if user_message:
            return (
                f"{base}\n"
                f"User query: {user_message}\n\n"
                f"AI Suggestion: Based on the current stage '{stage}' and a {probability}% probability, "
                f"consider {'prioritizing follow-up' if priority in ('high', 'critical') else 'nurturing the lead'}.\n"
                f"Recommended action: {'Schedule a demo or proposal meeting.' if stage in ('prospecting', 'qualification') else 'Prepare final terms and close.' if stage == 'negotiation' else 'Review and optimize strategy.'}"
            )

        if probability < 30:
            action = "Increase engagement with targeted content."
        elif probability < 60:
            action = "Schedule a follow-up meeting to address concerns."
        else:
            action = "Prepare contract and move to closing."

        return f"{base}\nAI Recommendation: {action}"

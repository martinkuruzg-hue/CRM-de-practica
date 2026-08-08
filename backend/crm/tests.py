from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Opportunity


class OpportunityAPITests(APITestCase):
    def setUp(self):
        self.opp = Opportunity.objects.create(
            company_name='Banco Andino',
            contact_name='Laura Pérez',
            contact_email='laura.perez@bancoandino.com',
            opportunity_name='Asistente IA para atención interna',
            estimated_value=85000.0,
            currency='USD',
            stage='Diagnóstico',
            priority='Alta',
            probability=65,
            owner='LABS IA',
        )

    def test_list_opportunities(self):
        url = reverse('opportunity-list')
        res = self.client.get(url, {'is_active': 'true'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.json()), 1)

    def test_create_opportunity(self):
        url = reverse('opportunity-list')
        res = self.client.post(url, {
            'company_name': 'Retail Nova',
            'contact_name': 'Carlos Ríos',
            'contact_email': 'carlos.rios@retailnova.com',
            'opportunity_name': 'Automatización comercial',
            'estimated_value': 42000.0,
            'currency': 'USD',
            'stage': 'Propuesta enviada',
            'priority': 'Media',
            'probability': 55,
            'owner': 'LABS IA',
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Opportunity.objects.filter(company_name='Retail Nova').exists())

    def test_create_invalid_email(self):
        url = reverse('opportunity-list')
        res = self.client.post(url, {
            'company_name': 'X',
            'contact_email': 'no-es-correo',
            'opportunity_name': 'Y',
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_detail(self):
        url = reverse('opportunity-detail', args=[self.opp.id])
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.json()['company_name'], 'Banco Andino')

    def test_update_opportunity(self):
        url = reverse('opportunity-detail', args=[self.opp.id])
        res = self.client.patch(url, {'stage': 'Negociación', 'probability': 80}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.opp.refresh_from_db()
        self.assertEqual(self.opp.stage, 'Negociación')

    def test_soft_delete(self):
        url = reverse('opportunity-detail', args=[self.opp.id])
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.opp.refresh_from_db()
        self.assertFalse(self.opp.is_active)

    def test_filter_by_stage(self):
        url = reverse('opportunity-list')
        res = self.client.get(url, {'stage': 'Diagnóstico'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.json()), 1)

    def test_search(self):
        url = reverse('opportunity-list')
        res = self.client.get(url, {'search': 'Banco'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.json()), 1)

    def test_stats(self):
        url = reverse('opportunity-stats')
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        body = res.json()
        self.assertEqual(body['total_opportunities'], 1)
        self.assertEqual(body['total_pipeline_value'], 85000.0)


class AssistantAPITests(APITestCase):
    def test_chat_returns_response(self):
        Opportunity.objects.create(
            company_name='Banco Andino',
            contact_name='Laura Pérez',
            contact_email='laura.perez@bancoandino.com',
            opportunity_name='Asistente IA',
            estimated_value=85000.0,
            currency='USD',
            stage='Diagnóstico',
            priority='Alta',
            probability=65,
            owner='LABS IA',
        )
        url = reverse('chat')
        res = self.client.post(url, {'message': 'Cual es el valor total del pipeline?'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        body = res.json()
        self.assertIn('assistant_response', body)
        self.assertTrue(body['assistant_response'])
        self.assertTrue(body['assistant_message_id'])

    def test_chat_requires_message(self):
        url = reverse('chat')
        res = self.client.post(url, {}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_chat_out_of_scope_controlled(self):
        url = reverse('chat')
        res = self.client.post(url, {'message': 'Cual es la capital de Francia?'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        body = res.json()
        self.assertIn('CRM', body['assistant_response'])

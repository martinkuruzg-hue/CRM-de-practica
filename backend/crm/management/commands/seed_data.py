import uuid
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from crm.models import Opportunity
from assistant.models import SystemPrompt


SYSTEM_PROMPT_V1 = """Eres un asistente experto en CRM para seguimiento comercial de proyectos de IA.

Tus capacidades:
1. Buscar y consultar oportunidades en el CRM.
2. Obtener detalles completos de oportunidades.
3. Actualizar el estado de oportunidades.
4. Proporcionar resúmenes y análisis del pipeline.
5. Listar oportunidades con seguimiento pendiente.

Siempre debes:
- Usar las herramientas disponibles cuando sea relevante.
- Basar tus respuestas EXCLUSIVAMENTE en datos reales del CRM.
- Indicar claramente cuando no tienes información suficiente.
- No inventar empresas, montos ni etapas que no aparezcan en el contexto.
- Responder en español, ser conciso y profesional.
- Explicar brevemente de dónde obtienes tus respuestas (ej: "según el CRM...").

Preguntas fuera del alcance del CRM: responde que solo puedes
ayudar con información comercial del CRM y ofrece opciones de consulta.

Contexto actual del CRM:
{rag_context}

Historial relevante:
{history_summary}"""


class Command(BaseCommand):
    help = 'Carga datos semilla de oportunidades (5 ejemplos de la prueba técnica)'

    def handle(self, *args, **options):
        today = date.today()

        def oid(name):
            return uuid.uuid5(uuid.NAMESPACE_DNS, f'crm-seed:{name}')

        data = [
            {
                'id': oid('Banco Andino'),
                'company_name': 'Banco Andino',
                'contact_name': 'Laura Pérez',
                'contact_email': 'laura.perez@bancoandino.com',
                'opportunity_name': 'Asistente IA para atención interna',
                'description': 'Implementación de un asistente de IA para consultas internas sobre políticas, procesos y documentos.',
                'estimated_value': 85000.0,
                'currency': 'USD',
                'stage': 'Diagnóstico',
                'priority': 'Alta',
                'probability': 65,
                'owner': 'LABS IA',
                'next_follow_up_date': today + timedelta(days=2),
                'last_interaction_summary': 'Cliente solicitó revisar alcance técnico y modelo de seguridad.',
                'ai_recommendation': 'Priorizar levantamiento de restricciones de datos y arquitectura cloud/local.',
                'is_active': True,
            },
            {
                'id': oid('Retail Nova'),
                'company_name': 'Retail Nova',
                'contact_name': 'Carlos Ríos',
                'contact_email': 'carlos.rios@retailnova.com',
                'opportunity_name': 'Automatización de seguimiento comercial con IA',
                'description': 'Sistema para registrar oportunidades, generar recordatorios y sugerir acciones comerciales.',
                'estimated_value': 42000.0,
                'currency': 'USD',
                'stage': 'Propuesta enviada',
                'priority': 'Media',
                'probability': 55,
                'owner': 'LABS IA',
                'next_follow_up_date': today + timedelta(days=5),
                'last_interaction_summary': 'Se envió propuesta inicial y se espera feedback del área de innovación.',
                'ai_recommendation': 'Enviar caso de uso comparable y reforzar beneficios de eficiencia.',
                'is_active': True,
            },
            {
                'id': oid('Minería Horizonte'),
                'company_name': 'Minería Horizonte',
                'contact_name': 'Patricia Gómez',
                'contact_email': 'patricia.gomez@mhorizonte.com',
                'opportunity_name': 'Modelo predictivo de mantenimiento',
                'description': 'Proyecto de IA para predecir fallas de maquinaria crítica utilizando datos históricos.',
                'estimated_value': 120000.0,
                'currency': 'USD',
                'stage': 'Negociación',
                'priority': 'Crítica',
                'probability': 80,
                'owner': 'Sebastián Saavedra',
                'next_follow_up_date': today + timedelta(days=1),
                'last_interaction_summary': 'Cliente validó alcance técnico y solicitó propuesta económica final.',
                'ai_recommendation': 'Acelerar cierre comercial y preparar plan de implementación inicial.',
                'is_active': True,
            },
            {
                'id': oid('Salud Integral'),
                'company_name': 'Salud Integral',
                'contact_name': 'Andrés Molina',
                'contact_email': 'andres.molina@saludintegral.com',
                'opportunity_name': 'Chatbot clínico interno',
                'description': 'Asistente conversacional para soporte interno del personal médico y administrativo.',
                'estimated_value': 65000.0,
                'currency': 'USD',
                'stage': 'Contactado',
                'priority': 'Alta',
                'probability': 40,
                'owner': 'LABS IA',
                'next_follow_up_date': today + timedelta(days=4),
                'last_interaction_summary': 'Cliente interesado en capacidades de seguridad y compliance.',
                'ai_recommendation': 'Enviar arquitectura híbrida y enfoque de protección de datos.',
                'is_active': True,
            },
            {
                'id': oid('Logística Global'),
                'company_name': 'Logística Global',
                'contact_name': 'María Fernández',
                'contact_email': 'maria.fernandez@logisticaglobal.com',
                'opportunity_name': 'Optimización logística con IA',
                'description': 'Sistema de análisis y recomendación de rutas utilizando modelos de optimización.',
                'estimated_value': 98000.0,
                'currency': 'USD',
                'stage': 'Lead nuevo',
                'priority': 'Media',
                'probability': 25,
                'owner': 'Carlos Bermúdez',
                'next_follow_up_date': today + timedelta(days=7),
                'last_interaction_summary': 'Se realizó reunión inicial con el área de operaciones.',
                'ai_recommendation': 'Profundizar en requerimientos de integración y fuentes de datos disponibles.',
                'is_active': True,
            },
        ]

        created = 0
        for item in data:
            _, was_created = Opportunity.objects.update_or_create(id=item['id'], defaults=item)
            created += 1 if was_created else 0

        prompt, prompt_created = SystemPrompt.objects.update_or_create(
            version='1',
            defaults={
                'name': 'CRM Comercial IA - v1',
                'content': SYSTEM_PROMPT_V1,
                'is_active': True,
                'changelog': 'Versión inicial del asistente de CRM con tool calling, RAG y control de alucinaciones.',
            },
        )
        SystemPrompt.objects.exclude(version='1').update(is_active=False)

        self.stdout.write(self.style.SUCCESS(
            f'Datos semilla cargados: {len(data)} oportunidades ({created} creadas), '
            f'prompt v{prompt.version} {"creado" if prompt_created else "actualizado"}'
        ))

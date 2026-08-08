import json
from crm.models import Opportunity

STAGES = ['Lead nuevo', 'Contactado', 'Diagnóstico', 'Propuesta enviada', 'Negociación', 'Ganado', 'Perdido']
PRIORITIES = ['Baja', 'Media', 'Alta', 'Crítica']


class ToolRegistry:
    def __init__(self):
        self._tools = {}
        self._register_builtins()

    def _register_builtins(self):
        self.register(
            name='search_opportunities',
            description='Search CRM opportunities by company name, contact, stage, or keywords',
            parameters={
                'type': 'object',
                'properties': {
                    'query': {
                        'type': 'string',
                        'description': 'Search query to find opportunities',
                    },
                    'stage': {
                        'type': 'string',
                        'enum': STAGES,
                        'description': 'Filter by stage',
                    },
                    'priority': {
                        'type': 'string',
                        'enum': PRIORITIES,
                        'description': 'Filter by priority',
                    },
                    'limit': {
                        'type': 'integer',
                        'description': 'Maximum results to return',
                        'default': 5,
                    },
                },
                'required': ['query'],
            },
            handler=self._search_opportunities,
        )
        self.register(
            name='get_opportunity_details',
            description='Get full details of a specific opportunity by ID',
            parameters={
                'type': 'object',
                'properties': {
                    'opportunity_id': {
                        'type': 'string',
                        'description': 'The opportunity ID',
                    },
                },
                'required': ['opportunity_id'],
            },
            handler=self._get_opportunity_details,
        )
        self.register(
            name='update_opportunity_stage',
            description='Update the stage of an opportunity',
            parameters={
                'type': 'object',
                'properties': {
                    'opportunity_id': {'type': 'string', 'description': 'The opportunity ID'},
                    'stage': {
                        'type': 'string',
                        'enum': STAGES,
                        'description': 'New stage',
                    },
                },
                'required': ['opportunity_id', 'stage'],
            },
            handler=self._update_stage,
        )
        self.register(
            name='get_crm_summary',
            description='Get a summary of all CRM opportunities',
            parameters={
                'type': 'object',
                'properties': {
                    'group_by': {
                        'type': 'string',
                        'enum': ['stage', 'priority', 'owner'],
                        'description': 'Group results by this field',
                        'default': 'stage',
                    },
                },
            },
            handler=self._get_summary,
        )
        self.register(
            name='get_follow_ups',
            description='Get opportunities that need follow-up in the next 7 days',
            parameters={
                'type': 'object',
                'properties': {},
            },
            handler=self._get_follow_ups,
        )

    def register(self, name, description, parameters, handler):
        self._tools[name] = {
            'name': name,
            'description': description,
            'parameters': parameters,
            'handler': handler,
        }

    def get_tool_definitions(self):
        return [
            {
                'type': 'function',
                'function': {
                    'name': t['name'],
                    'description': t['description'],
                    'parameters': t['parameters'],
                },
            }
            for t in self._tools.values()
        ]

    def execute(self, tool_name, arguments):
        if tool_name not in self._tools:
            return json.dumps({'error': f'Tool "{tool_name}" not found'})

        args = json.loads(arguments) if isinstance(arguments, str) else arguments
        handler = self._tools[tool_name]['handler']
        try:
            result = handler(**args)
            return json.dumps(result, ensure_ascii=False, default=str)
        except Exception as e:
            return json.dumps({'error': str(e)})

    def _search_opportunities(self, query, stage=None, priority=None, limit=5):
        qs = Opportunity.objects.filter(is_active=True)
        if stage:
            qs = qs.filter(stage=stage)
        if priority:
            qs = qs.filter(priority=priority)

        results = []
        for opp in qs[:limit]:
            results.append(self._opp_to_dict(opp))
        return {'results': results, 'total': qs.count()}

    def _get_opportunity_details(self, opportunity_id):
        try:
            opp = Opportunity.objects.get(id=opportunity_id, is_active=True)
            return self._opp_to_dict(opp, detailed=True)
        except Opportunity.DoesNotExist:
            return {'error': 'Opportunity not found'}

    def _update_stage(self, opportunity_id, stage):
        try:
            opp = Opportunity.objects.get(id=opportunity_id)
            opp.stage = stage
            opp.save()
            return {'success': True, 'opportunity_id': str(opportunity_id), 'new_stage': stage}
        except Opportunity.DoesNotExist:
            return {'error': 'Opportunity not found'}

    def _get_summary(self, group_by='stage'):
        qs = Opportunity.objects.filter(is_active=True)
        groups = {}
        for opp in qs:
            key = getattr(opp, group_by, 'unknown')
            if key not in groups:
                groups[key] = {'count': 0, 'total_value': 0.0, 'items': []}
            groups[key]['count'] += 1
            groups[key]['total_value'] += opp.estimated_value
            groups[key]['items'].append(opp.opportunity_name)

        return {
            'group_by': group_by,
            'total_opportunities': qs.count(),
            'total_value': sum(o.estimated_value for o in qs),
            'groups': groups,
        }

    def _get_follow_ups(self, days=7):
        from datetime import date, timedelta
        today = date.today()
        end = today + timedelta(days=days)
        qs = Opportunity.objects.filter(
            is_active=True,
            next_follow_up_date__gte=today,
            next_follow_up_date__lte=end,
        ).exclude(stage__in=['Ganado', 'Perdido']).order_by('next_follow_up_date')
        return {
            'window_days': days,
            'total': qs.count(),
            'items': [
                {
                    'id': str(o.id),
                    'company_name': o.company_name,
                    'opportunity_name': o.opportunity_name,
                    'stage': o.stage,
                    'priority': o.priority,
                    'probability': o.probability,
                    'next_follow_up_date': o.next_follow_up_date.isoformat() if o.next_follow_up_date else None,
                    'owner': o.owner,
                }
                for o in qs
            ],
        }

    def _opp_to_dict(self, opp, detailed=False):
        data = {
            'id': opp.id,
            'company_name': opp.company_name,
            'opportunity_name': opp.opportunity_name,
            'stage': opp.stage,
            'priority': opp.priority,
            'estimated_value': opp.estimated_value,
            'currency': opp.currency,
            'probability': opp.probability,
            'contact_name': opp.contact_name,
        }
        if detailed:
            data.update({
                'contact_email': opp.contact_email,
                'description': opp.description,
                'owner': opp.owner,
                'next_follow_up_date': opp.next_follow_up_date,
                'last_interaction_summary': opp.last_interaction_summary,
            })
        return data

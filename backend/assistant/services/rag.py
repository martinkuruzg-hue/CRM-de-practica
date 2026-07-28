import re
from crm.models import Opportunity


class RAGService:
    def __init__(self):
        self.fields = [
            'company_name', 'contact_name', 'contact_email',
            'opportunity_name', 'description', 'stage',
            'priority', 'owner', 'estimated_value', 'currency',
        ]

    def _tokenize(self, text):
        return set(re.sub(r'[^\w\s]', '', text.lower()).split())

    def _score_opportunity(self, opp, query_tokens):
        score = 0.0
        text = ' '.join(str(getattr(opp, f, '')) for f in self.fields).lower()
        text_tokens = self._tokenize(text)
        matches = query_tokens & text_tokens
        score += len(matches) * 2.0

        query_lower = query_tokens

        if query_lower & {'high', 'critical'} and opp.priority in ('high', 'critical'):
            score += 5.0
        if query_lower & {'closed', 'won', 'lost'} and opp.stage in ('closed_won', 'closed_lost'):
            score += 5.0
        if query_lower & {'prospecting', 'qualification', 'proposal', 'negotiation'}:
            if opp.stage in query_lower:
                score += 5.0

        value_terms = {'gran', 'alto', 'valioso', 'importante', 'grande'}
        if value_terms & query_lower:
            if opp.estimated_value > 50000:
                score += 3.0

        return score

    def search(self, query, top_k=5, min_score=1.0):
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        opportunities = Opportunity.objects.filter(is_active=True)
        scored = []

        for opp in opportunities:
            score = self._score_opportunity(opp, query_tokens)
            if score >= min_score:
                scored.append((score, opp))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [opp for score, opp in scored[:top_k]]

    def format_context(self, opportunities):
        if not opportunities:
            return ''

        lines = ['CRM Context:']
        for i, opp in enumerate(opportunities, 1):
            lines.append(
                f'{i}. {opp.opportunity_name} | Company: {opp.company_name} | '
                f'Contact: {opp.contact_name} ({opp.contact_email}) | '
                f'Stage: {opp.stage} | Priority: {opp.priority} | '
                f'Value: {opp.estimated_value} {opp.currency} | '
                f'Probability: {opp.probability}% | '
                f'Owner: {opp.owner}'
            )
        return '\n'.join(lines)

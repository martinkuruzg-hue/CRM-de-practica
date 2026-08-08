import re


class HallucinationController:
    def __init__(self):
        self.source_data = {}

    def set_source_context(self, rag_context, tool_results=None):
        self.source_data = {
            'rag_context': rag_context,
            'tool_results': tool_results or [],
        }

    def _extract_factual_claims(self, text):
        claims = []
        patterns = [
            r'(\d[\d,]*\.?\d*)\s*(USD|EUR|MXN|dollars|euros)',
            r'(probability|probabilidad|porcentaje)\s*(?:de\s*)?(?:is|:)?\s*(\d+)%',
            r'(stage|etapa)\s*(?:is|:)?\s*["\']?(\w+)["\']?',
            r'(priority|prioridad)\s*(?:is|:)?\s*["\']?(\w+)["\']?',
            r'\b(company|empresa)\b\s*[:=]?\s*["\']?([^"\'.,\n]+)["\']?',
            r'\b(contact|contacto)\b\s*[:=]?\s*["\']?([^"\'.,\n]+)["\']?',
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            claims.extend(matches)
        return claims

    def _check_claim_against_source(self, claim, source_text):
        claim_text = ' '.join(claim).lower()
        source_lower = source_text.lower()
        words = re.sub(r'[^\w\s]', '', claim_text).split()
        if len(words) <= 1:
            return True

        matches = sum(1 for w in words if len(w) > 2 and w in source_lower)
        return matches >= max(1, len(words) - 1)

    def evaluate(self, assistant_response, rag_context, tool_results=None):
        if not rag_context and not tool_results:
            return {'score': 1.0, 'warnings': [], 'is_safe': True}

        source_text = (rag_context or '') + '\n' + '\n'.join(
            str(r) for r in (tool_results or [])
        )

        claims = self._extract_factual_claims(assistant_response)
        warnings = []
        unsupported = 0
        total = len(claims)

        for claim in claims:
            if not self._check_claim_against_source(claim, source_text):
                unsupported += 1
                warnings.append(f'Unsupported claim: {" ".join(claim)}')

        score = 1.0 - (unsupported / max(total, 1)) * 0.5

        return {
            'score': round(max(0.0, score), 2),
            'warnings': warnings,
            'total_claims_checked': total,
            'unsupported_claims': unsupported,
            'is_safe': unsupported == 0,
        }

    def add_hallucination_guard(self, response_text):
        guard = (
            '\n\n[Nota IA: La información anterior se basa en los datos del CRM disponibles al momento '
            'de la respuesta. Para decisiones críticas, verifique directamente con el contacto o el sistema.]'
        )
        return response_text + guard

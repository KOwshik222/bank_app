"""
Knowledge & Runbook Agent — queries the RAG system to find relevant runbooks and past incidents.
"""

from typing import Any
from ai.agents.base_agent import AgentResult, BaseAgent
from ai.llm.prompt_templates import KNOWLEDGE_RAG_PROMPT, SYSTEM_BASE_PROMPT
from ai.rag.retriever import KnowledgeRetriever


class KnowledgeRAGAgent(BaseAgent):
    """Specialized agent that searches vector knowledge base for operational runbooks and past incidents."""

    def __init__(self):
        super().__init__(
            name="KnowledgeRAGAgent",
            role_description="Searches runbooks and past resolved incidents using Qdrant vector retrieval.",
        )
        self.retriever = KnowledgeRetriever()

    async def investigate(self, context: dict[str, Any]) -> AgentResult:
        title = context.get("title", "Service incident")
        description = context.get("description", "")
        service = context.get("affected_service", "payment-service")

        query = f"{title} {description} {service}"
        runbook_hits = self.retriever.search_runbooks(query, limit=2)
        incident_hits = self.retriever.search_historical_incidents(query, limit=2)

        all_hits = runbook_hits + incident_hits
        citations = [h["citation"] for h in all_hits]

        docs_summary = "\n\n".join([
            f"Document: {h['title']} ({h['citation']}) [Score: {h['relevance_score']:.2f}]\n{h['content'][:400]}..."
            for h in all_hits
        ])

        user_prompt = KNOWLEDGE_RAG_PROMPT.format(
            title=title,
            description=description,
            retrieved_docs=docs_summary or "No matching documentation found",
        )

        llm_response = await self.llm.chat(SYSTEM_BASE_PROMPT, user_prompt)

        evidence = []
        for hit in all_hits:
            evidence.append(f"Retrieved: {hit['citation']} (similarity: {hit['relevance_score']:.2f})")

        top_runbook = runbook_hits[0]["title"] if runbook_hits else "Standard Operations Manual"
        resolution = llm_response.get("established_resolution") or (
            runbook_hits[0]["content"].split("## Remediation")[-1][:200] if runbook_hits else "Follow standard recovery"
        )

        return AgentResult(
            agent_name=self.name,
            hypothesis=f"Matched operational runbook: {top_runbook}",
            confidence=0.93 if all_hits else 0.70,
            evidence=evidence,
            data={
                "citations": citations,
                "hits": all_hits,
                "top_runbook": top_runbook,
            },
            recommendation=resolution,
        )

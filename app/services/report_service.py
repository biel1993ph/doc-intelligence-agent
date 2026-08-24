"""Serviço de geração de relatório Markdown."""


REPORT_SECTIONS_ORDER = [
    "resumo",
    "escopo",
    "pontos_fortes",
    "problemas",
    "checklist",
    "nota",
    "limitacoes",
]


def generate_report_markdown(
    analysis_result: dict,
    discovered_files: list[str] | None = None,
    repository_metadata: dict | None = None,
    analysis_history: list[dict] | None = None,
) -> str:
    """Gera relatório Markdown estruturado a partir do resultado da análise.

    Seções em ordem:
    1. Resumo
    2. Informações do Repositório (se metadados disponíveis)
    3. Escopo
    4. Pontos Fortes
    5. Problemas
    6. Checklist de Melhorias
    7. Nota
    8. Limitações

    Args:
        analysis_result: Dicionário com resultado da análise.
        discovered_files: Lista de arquivos analisados (para rastreabilidade).
        repository_metadata: Metadados do repositório GitHub (opcional).

    Returns:
        String Markdown do relatório completo.
    """
    sections: list[str] = []

    # 1. Resumo
    sections.append("# Relatório de Análise de Documentação\n")
    base_insuficiente = analysis_result.get("base_insuficiente", False)
    if base_insuficiente:
        sections.append("⚠️ **Base documental insuficiente** — avaliação limitada.\n")
    else:
        sections.append("Análise completa da documentação do projeto.\n")

    # 2. Informações do Repositório (se disponível)
    if repository_metadata:
        sections.append("## Informações do Repositório\n")
        sections.append("| Campo | Valor |")
        sections.append("|-------|-------|")
        sections.append(f"| Nome | {repository_metadata.get('full_name', 'N/A')} |")
        if repository_metadata.get("description"):
            sections.append(f"| Descrição | {repository_metadata['description']} |")
        if repository_metadata.get("language"):
            sections.append(f"| Linguagem | {repository_metadata['language']} |")
        sections.append(f"| Stars | {repository_metadata.get('stars', 0)} |")
        sections.append(f"| Forks | {repository_metadata.get('forks', 0)} |")
        sections.append(f"| Issues abertas | {repository_metadata.get('open_issues', 0)} |")
        sections.append(f"| Branch padrão | {repository_metadata.get('default_branch', 'main')} |")
        if repository_metadata.get("pushed_at"):
            sections.append(f"| Último push | {repository_metadata['pushed_at']} |")
        if repository_metadata.get("topics"):
            topics_str = ", ".join(repository_metadata["topics"])
            sections.append(f"| Tópicos | {topics_str} |")
        sections.append("")

    # 3. Escopo
    sections.append("## Escopo\n")
    if discovered_files:
        sections.append("Arquivos analisados:\n")
        for f in discovered_files:
            # Usar apenas o nome do arquivo para clareza
            from pathlib import Path
            sections.append(f"- `{Path(f).name}`")
        sections.append("")
    else:
        sections.append("Nenhum arquivo de escopo disponível.\n")

    # 3. Pontos Fortes
    sections.append("## Pontos Fortes\n")
    strengths = analysis_result.get("strengths", [])
    if strengths:
        for s in strengths:
            sections.append(f"- ✅ {s}")
    else:
        sections.append("- Nenhum ponto forte identificado.")
    sections.append("")

    # 4. Problemas
    sections.append("## Problemas Identificados\n")
    issues = analysis_result.get("issues", [])
    if issues:
        for i, issue in enumerate(issues, 1):
            obs = issue.get("observation", "")
            rec = issue.get("recommendation", "")
            sections.append(f"### {i}. {obs}\n")
            sections.append(f"**Recomendação:** {rec}\n")
    else:
        sections.append("Nenhum problema identificado.\n")

    # 5. Checklist de Melhorias
    sections.append("## Checklist de Melhorias\n")
    if issues:
        for issue in issues:
            rec = issue.get("recommendation", "")
            sections.append(f"- [ ] {rec}")
    else:
        sections.append("- [x] Documentação aparenta estar completa.")
    sections.append("")

    # 6. Nota
    sections.append("## Nota\n")
    score = analysis_result.get("score", 0)
    justification = analysis_result.get("justification", "")
    sections.append(f"**{score}/10**\n")
    sections.append(f"{justification}\n")

    # Dimensões
    dimensions = analysis_result.get("dimensions", {})
    if dimensions:
        sections.append("| Dimensão | Avaliação |")
        sections.append("|----------|-----------|")
        for dim, val in dimensions.items():
            sections.append(f"| {dim.capitalize()} | {val} |")
        sections.append("")

    # 7. Histórico (se há análises anteriores)
    if analysis_history:
        sections.append("## Histórico\n")
        current_score = analysis_result.get("score", 0)
        prev_score = analysis_history[0].get("score", 0)
        prev_date = analysis_history[0].get("analyzed_at", "desconhecida")[:10]

        sections.append(f"**Evolução:** nota anterior {prev_score} → nota atual {current_score}\n")
        sections.append(f"Última análise: {prev_date}\n")

        if len(analysis_history) > 1:
            sections.append("| Data | Nota | Problemas | Pontos fortes |")
            sections.append("|------|------|-----------|---------------|")
            for record in analysis_history[:5]:
                date = record.get("analyzed_at", "")[:10]
                score = record.get("score", 0)
                findings = record.get("findings_count", 0)
                strengths = record.get("strengths_count", 0)
                sections.append(f"| {date} | {score}/10 | {findings} | {strengths} |")
            sections.append("")
        sections.append("")

    # 8. Limitações
    sections.append("## Limitações\n")
    limitations = [
        "Análise baseada exclusivamente no conteúdo textual disponível.",
        "Não avalia precisão técnica do conteúdo (apenas estrutura e completude).",
        "Contexto limitado ao que foi descoberto nos arquivos Markdown.",
    ]
    if base_insuficiente:
        limitations.insert(0, "Base documental insuficiente para avaliação completa.")
    for lim in limitations:
        sections.append(f"- {lim}")
    sections.append("")

    return "\n".join(sections)

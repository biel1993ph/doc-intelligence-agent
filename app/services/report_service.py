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


def generate_report_markdown(analysis_result: dict, discovered_files: list[str] | None = None) -> str:
    """Gera relatório Markdown estruturado a partir do resultado da análise.

    Seções em ordem:
    1. Resumo
    2. Escopo
    3. Pontos Fortes
    4. Problemas
    5. Checklist de Melhorias
    6. Nota
    7. Limitações

    Args:
        analysis_result: Dicionário com resultado da análise.
        discovered_files: Lista de arquivos analisados (para rastreabilidade).

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

    # 2. Escopo
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

    # 7. Limitações
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

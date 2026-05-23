from accessibility.contracts import WCAGCriterion, ConformanceLevel

WCAG_CATALOG: list[WCAGCriterion] = [
    WCAGCriterion("1.1.1", ConformanceLevel.A,  "Conteúdo não-textual precisa de alternativa em texto", "WCAG 2.1"),
    WCAGCriterion("1.3.1", ConformanceLevel.A,  "Informação e relações transmitidas visualmente devem ser preservadas programaticamente", "WCAG 2.1"),
    WCAGCriterion("1.4.1", ConformanceLevel.A,  "Cor não deve ser o único meio de transmitir informação", "WCAG 2.1"),
    WCAGCriterion("2.1.1", ConformanceLevel.A,  "Toda funcionalidade deve ser operável via teclado", "WCAG 2.1"),
    WCAGCriterion("3.3.1", ConformanceLevel.A,  "Erros de entrada identificados e descritos ao usuário", "WCAG 2.1"),
    WCAGCriterion("3.3.2", ConformanceLevel.A,  "Rótulos ou instruções fornecidos onde o conteúdo requer entrada", "WCAG 2.1"),
    WCAGCriterion("4.1.2", ConformanceLevel.A,  "Nome, função e valor de componentes de UI acessíveis programaticamente", "WCAG 2.1"),
    WCAGCriterion("1.4.3", ConformanceLevel.AA, "Contraste mínimo de 4.5:1 para texto normal", "WCAG 2.1"),
    WCAGCriterion("1.4.4", ConformanceLevel.AA, "Texto redimensionável até 200% sem perda de conteúdo", "WCAG 2.1"),
    WCAGCriterion("2.4.6", ConformanceLevel.AA, "Cabeçalhos e rótulos descritivos", "WCAG 2.1"),
    WCAGCriterion("2.4.7", ConformanceLevel.AA, "Foco visível em componentes operáveis por teclado", "WCAG 2.1"),
    WCAGCriterion("3.3.3", ConformanceLevel.AA, "Sugestão de erro fornecida quando possível", "WCAG 2.1"),
    WCAGCriterion("3.3.4", ConformanceLevel.AA, "Prevenção de erros em ações legais, financeiras ou de dados", "WCAG 2.1"),
    WCAGCriterion("3.3.8", ConformanceLevel.AA, "Autenticação acessível sem teste cognitivo", "WCAG 2.2"),
]

NIELSEN_HEURISTICS: list[tuple[int, str, list[str]]] = [
    (1,  "Visibilidade do status do sistema",     ["status","progresso","feedback","carregamento"]),
    (2,  "Correspondência com o mundo real",       ["linguagem","terminologia","vocabulário"]),
    (3,  "Controle e liberdade do usuário",        ["cancelar","desfazer","voltar","sair"]),
    (4,  "Consistência e padrões",                 ["consistente","padrão","convenção"]),
    (5,  "Prevenção de erros",                     ["validação","confirmação","prevenção"]),
    (6,  "Reconhecimento em vez de memorização",   ["visível","disponível","sugestão"]),
    (7,  "Flexibilidade e eficiência de uso",      ["atalho","personalização","avançado"]),
    (8,  "Design estético e minimalista",          ["exibir","mostrar","visualmente"]),
    (9,  "Reconhecimento, diagnóstico e recuperação",["erro","falha","mensagem","recuperar"]),
    (10, "Ajuda e documentação",                   ["ajuda","documentação","tutorial"]),
]

_UI_KEYWORDS = [
    "tela","interface","formulário","botão","campo","modal","menu","listagem",
    "exibir","mostrar","visualizar","dashboard","input","upload","download",
    "notificação","alerta","mensagem",
]

# InfraClima — redesign e validação da interface

> **Registro histórico:** este relatório descreve o redesign visual feito antes da integração Full Stack. As informações sobre execução só no navegador, ausência de API/banco e QA do redesign são referentes àquela etapa. Para a versão atual, consulte `README.md` e `IMPLEMENTACAO_FULLSTACK.md`.

Revisão visual de 14/10/2026 (America/Manaus).

## Diagnóstico e decisões

A interface anterior apresentava seis áreas funcionais: visão geral, mapa, grafo espacial, análise, dados/exportação e descrição do método. Os painéis tinham pesos visuais semelhantes, os parâmetros eram comprimidos em três colunas e os símbolos da navegação não seguiam o mesmo estilo. O menu móvel não tinha fechamento explícito, controle de foco ou indicação de expansão.

O redesign mantém os textos, indicadores, tabelas, filtros, campos, ações e cálculos. A apresentação foi reorganizada com cabeçalho contextual, navegação lateral persistente, ícones SVG padronizados, cards de indicadores e configuração dividida em blocos. A paleta usa verde-petróleo e tons claros de vegetação; as cores dos clusters continuam sendo as mesmas categorias do algoritmo. O motivo de rede no cabeçalho é exclusivamente decorativo, identificado como tal para tecnologias assistivas.

## Mudanças implementadas

- Sistema de espaçamento, hierarquia tipográfica, bordas, estados de foco, superfícies e botões consistente entre as páginas.
- Maior área de mapa no desktop, parâmetros com rótulos legíveis e raio geográfico separado das variáveis padronizadas do DBSCAN.
- Tabelas com cabeçalhos fixos, números alinhados e rolagem local em telas pequenas, sem esconder colunas ou descartar dados.
- Rótulos do grafo reposicionados para reduzir sobreposição, com linhas-guia quando necessário; todos os identificadores continuam presentes e os nós mantêm suas posições geográficas relativas. Em telas pequenas, o grafo tem rolagem local para manter a leitura.
- Menu móvel com botão de fechar, fechamento por Escape, controle de foco, fundo interativo e estado acessível de expansão.
- Link para pular a navegação, identificação das regiões tabulares e respeito à preferência de redução de movimento.
- Feedback de importação em andamento associado à operação real, mensagens de conclusão e erros preservadas.
- Aviso quando há falha de carregamento de blocos cartográficos externos. A interface não apresenta uma base simulada como se fosse um mapa real.
- Correção do enquadramento do mapa ao mostrar uma aba oculta e ao redimensionar o painel. O observador recalcula apenas a apresentação; não altera dados, distâncias, rótulos ou métricas.
- Página `Visualizar_InfraClima.html` para abrir o mesmo front diretamente no navegador. Os módulos em `src/` continuam sendo a fonte de desenvolvimento.

## Preservação verificada

Uma cópia da versão anterior foi usada como referência antes da edição. A comparação em navegador confirmou:

- preservação dos 611 nós textuais originais comparados, excluindo símbolos decorativos substituídos por SVG;
- preservação dos 17 campos e seletores existentes, incluindo identificadores, valores iniciais, limites, passos e formatos aceitos;
- manutenção das seis páginas e dos identificadores usados pela aplicação;
- igualdade das exportações CSV de nós, arestas e resumo;
- igualdade estrutural e numérica do GeoJSON, desconsiderando apenas o horário de exportação;
- igualdade dos resultados da visualização em arquivo único e da versão modular;
- nenhum ajuste nos módulos de clusterização, estatísticas, processamento de dados ou análise do grafo.

As mudanças em `main.js` limitam-se ao redimensionamento e reenquadramento visual do mapa. A nova camada `design.js` não executa DBSCAN nem modifica o estado dos dados.

## Validação executada

- Oito testes automatizados do núcleo passaram.
- Navegação, reexecução com parâmetros diferentes, filtros de grupo, camadas do mapa, seleção de nó por teclado, importação CSV válida, rejeição de importação inválida preservando a análise anterior e restauração da demonstração foram exercitadas em Chromium 153.
- Os quatro caminhos de exportação foram acionados e os arquivos comparados com a versão anterior.
- Foram verificadas as seis páginas em 320, 390, 768, 1024 e 1440 pixels: 30 combinações sem rolagem horizontal do documento. Tabelas extensas mantêm rolagem própria.
- Foram realizadas 12 verificações automatizadas de acessibilidade com axe-core: seis páginas no desktop e seis no celular, com regras WCAG 2 A/AA e WCAG 2.1 AA. A execução final não apontou violações nessas regras. Isso não equivale a certificação completa ou avaliação com pessoas com deficiência.
- Não foram registrados erros JavaScript de página nos fluxos testados.
- A página de arquivo único foi aberta por `file://` e validada sem servidor local.

## Limitações e pendências

1. As verificações de navegador desta etapa usaram Chromium; Firefox, Safari e dispositivos físicos ainda precisam de validação.
2. Não foi realizado teste de usabilidade com participantes nem avaliação manual com leitores de tela.
3. Os servidores externos de tiles não responderam em parte da execução de QA. Foram conferidos o posicionamento das observações e o estado de falha; não foi validado o conteúdo cartográfico remoto. A biblioteca Leaflet usada no teste foi a mesma versão 1.9.4 fixada no projeto.
4. Os dados iniciais continuam sintéticos. O redesign não acrescenta observações reais, sensores, API, banco de dados ou resultados empíricos sobre Manaus.
5. Permanecem as limitações metodológicas e de qualidade de entrada registradas no README e no diagnóstico funcional. Esta revisão visual não valida cientificamente os parâmetros do DBSCAN nem as fontes importadas.

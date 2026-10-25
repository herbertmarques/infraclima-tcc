# Revisão de conformidade do front end InfraClima

> **Diagnóstico histórico pré-Full Stack:** as pendências e a arquitetura descritas abaixo registram o estado do protótipo antes da implementação FastAPI/SQLite. O estado atual está documentado em `README.md` e `IMPLEMENTACAO_FULLSTACK.md`.

## Resultado da inspeção da versão anterior

O pacote `InfraClima-frontend.zip` da Biblioteca, datado de 11/09/2026, era um dashboard React/Vite para telemetria. Ele mostrava sensores, umidade, infraestrutura e degradações com valores fixos, mas não implementava DBSCAN, grafo espacial, importação de CSV/GeoJSON ou análise reproduzível. Esses elementos contrariavam o escopo sem sensores físicos e poderiam ser confundidos com dados observados. A descrição de interface em `InfraClima_FrontEnd(1).docx` e os requisitos RF/RNF descrevem outro protótipo, em HTML/CSS/JavaScript, que calcula DBSCAN e grafo no navegador. O documento de interface ainda informa que exportação CSV está pendente; nesta reconstrução, CSV de nós, arestas e resumo foram implementados, então esse documento precisa ser atualizado antes de ser apresentado como descrição da nova versão.

A versão reconstruída neste pacote remove os indicadores de sensores e degradação e passa a implementar o fluxo documentado de importação, agrupamento, grafo, visualização e exportação. Ela continua sendo um protótipo de navegador com dados sintéticos iniciais, não o sistema científico concluído nem o backend Python descrito em UML.

## Matriz resumida de requisitos funcionais

| Requisito | Situação no protótipo | Observação técnica |
|---|---|---|
| RF01 — carregar CSV/GeoJSON | Parcial | Lê os dois formatos e registra metadados informados. Não valida automaticamente origem, licença ou se a área é Manaus. |
| RF02 — tratar e padronizar dados | Parcial | Descarta coordenadas/temperaturas inválidas e duplicatas exatas; pressupõe WGS 84 e °C. Não reprojeta CRS nem converte unidades. |
| RF03 — análise exploratória | Parcial | Exibe contagens, média, mínimo, máximo, desvio padrão, histograma térmico e perfis por grupo. Ainda não resume todas as variáveis possíveis do conjunto. |
| RF04–RF05 — nós, arestas e critério espacial | Implementado no protótipo | Nós correspondem a observações; arestas usam distância Haversine e raio em quilômetros. |
| RF06–RF07 — DBSCAN e rótulos | Implementado no protótipo | Variáveis selecionáveis são padronizadas; `eps` opera no espaço de atributos Z-score e o ruído recebe rótulo −1. |
| RF08–RF09 — métricas e distribuição espacial | Implementado no protótipo | Calcula grau, vizinhos, componentes, composição dos componentes e arestas entre rótulos. |
| RF10 — perfil térmico por grupo | Implementado no protótipo | Média, mínimo, máximo e desvio padrão populacional da temperatura importada. |
| RF11 — avaliação da clusterização | Parcial | Silhouette é calculado sem ruído, quando há dois ou mais grupos, e limitado a 220 pontos por custo quadrático; fora dessas condições, mostra N/A. |
| RF12 — mapa web | Parcial | Leaflet/OpenStreetMap apresenta nós, halos por grupo e arestas. Requer acesso aos recursos externos para o mapa base. |
| RF13 — consultar nó/grupo | Parcial | Nó mostra atributos, grupo, vizinhos, grau e componente; grupos possuem perfil agregado em tabela e análise. |
| RF14 — camadas e filtros | Implementado no protótipo | Permite ligar/desligar nós, halos de grupo e arestas, além de filtrar por grupo. |
| RF15 — reexecutar experimento | Implementado no protótipo | Permite mudar `eps`, `min_samples`, raio do grafo e variáveis e recalcular a execução. |
| RF16 — exportar resultados | Implementado no protótipo | Exporta GeoJSON completo, CSV de nós, CSV de arestas e CSV de resumo. |
| RF17 — API FastAPI | Não incluído | Requisito desejável. Esta versão opera localmente no navegador e não depende de API. |

## Requisitos não funcionais e arquitetura

- **RNF01 reprodutibilidade — parcial:** parâmetros, variáveis e data da exportação são registrados. O pacote não fixa hash do conjunto de entrada nem registra hash/versão do código em cada execução. O DBSCAN implementado é determinístico para a mesma entrada e parâmetros.
- **RNF02 dados abertos — condicional ao operador:** a interface não coleta de sensores e pede origem/licença/período, mas não comprova que o arquivo seja aberto ou adequado.
- **RNF03 rastreabilidade — parcial:** as quantidades de inválidos e duplicatas são exibidas e exportadas; o sistema não mantém arquivo de log linha a linha nem preserva a versão bruta após fechar a página.
- **RNF04 desempenho — não validado:** há limite de 800 linhas, mas ainda é necessário medir tempo e memória em computador de referência. DBSCAN e grafo usam cálculos quadráticos no pior caso.
- **RNF05 usabilidade — parcial:** rótulos em português e avisos metodológicos estão presentes; não houve teste com participantes.
- **RNF06 compatibilidade — não validada:** JavaScript moderno e layout responsivo foram implementados; faltam testes em Chrome, Firefox e Edge e revisão formal de acessibilidade.
- **RNF07 manutenibilidade — parcial:** leitura de dados, clusterização, grafo, estatísticas, orquestração e interface foram separados em módulos JavaScript. PEP 8 é convenção Python e deve aplicar-se ao backend planejado, não ao front JavaScript.
- **RNF08 extensibilidade — parcial:** módulos separam responsabilidades, mas os padrões Strategy, Adapter e Observer documentados como propostas não foram formalmente implementados como contratos/classes.
- **RNF09 interoperabilidade — parcial:** importação/exportação CSV/GeoJSON respeita ordem de coordenadas GeoJSON e declara CRS84 na exportação; não transforma CRS de entrada e pressupõe WGS 84.
- **RNF10 documentação — implementado para este pacote:** README documenta execução, campos, premissas, algoritmos e limitações.
- **RNF11 validade metodológica — parcial:** a tela informa limitações e não classifica grupos como risco. A calibração de parâmetros e validação de dados reais permanecem trabalho experimental.
- **RNF12 segurança e privacidade — compatível com o protótipo:** não há login, coleta de dados pessoais, API ou armazenamento remoto. Arquivos permanecem na memória da página.
- **RNF13 custo e infraestrutura — compatível:** processamento local e recursos de código aberto; a visualização cartográfica depende de internet para CDN e tiles OSM.
- **RNF14 prazo — fora da avaliação do artefato:** cronograma e marcos de conclusão devem ser controlados no documento de gestão do TCC.

## Pontos que ainda precisam ser decididos para o TCC

1. Definir um conjunto real e documentado referente a Manaus, verificar sua licença, período, cobertura, resolução e unidade. Nenhum dado de demonstração deve ser apresentado como resultado empírico.
2. Definir se a versão final será processada em JavaScript no navegador ou migrada para Python, scikit-learn e NetworkX. O artigo, o diagrama UML e o software precisam descrever a mesma arquitetura. FastAPI permanece opcional nos requisitos.
3. Justificar a seleção de variáveis e a padronização do DBSCAN, e explicar que `eps` não é distância em quilômetros. O raio do grafo é um parâmetro independente.
4. Executar os cenários do plano de testes no navegador e registrar ambiente, evidência, parâmetros e resultado. A validação atual cobriu oito testes unitários do núcleo e respostas HTTP 200 para a estrutura e os módulos; não foi realizada inspeção visual automatizada, pois o runtime disponível não tinha Chromium instalado.
5. Avaliar o algoritmo com dados reais e discutir as limitações de Silhouette para DBSCAN e para observações espaciais autocorrelacionadas.

**Conclusão da revisão:** o front reconstruído está substancialmente mais alinhado ao escopo e aos RFs que a versão React de monitoramento. A conformidade é de protótipo funcional; fonte real, validação empírica, testes entre navegadores, benchmark e fechamento da arquitetura continuam pendentes.

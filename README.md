# InfraClima Full Stack

Aplicação acadêmica para importar, armazenar, analisar e visualizar observações térmicas georreferenciadas, com foco exploratório em Manaus. A aplicação tem frontend web, API FastAPI e banco SQLite local. Os dados iniciais são sintéticos, reprodutíveis e identificados na interface; não representam medições reais. A geração usa semente padrão `42`; a API aceita uma semente diferente em `POST /api/datasets/demo?seed=123`.

## Executar no Windows

1. Instale Python 3.10 ou superior.
2. Extraia o ZIP.
3. Abra a pasta `InfraClima_MVP` e execute `iniciar_infraclima.bat`.
4. Na primeira execução, o script cria um ambiente isolado e instala as dependências. Depois abre `http://127.0.0.1:8000` no navegador.
5. Para encerrar, pressione `Ctrl+C` na janela do servidor.

O script `iniciar_infraclima.sh` prepara e inicia o projeto no Linux e macOS. Também é possível instalar manualmente com `python -m venv .venv`, ativar o ambiente, executar `pip install -r requirements.txt` e iniciar com `python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000`.

`Visualizar_InfraClima.html` e `npm run preview:build` fornecem uma página-guia para abrir o aplicativo local. A interface funcional depende do backend e deve ser acessada em `http://127.0.0.1:8000`.

O backend serve a interface e a API na mesma origem. Processamento, importação, banco e exportação não dependem de serviços externos. O mapa de fundo usa Leaflet e blocos do OpenStreetMap pela internet; se estiver sem conexão, as tabelas, o grafo SVG, análises e exportações continuam disponíveis.

## Fluxo da demonstração

1. Inicie o InfraClima pelo script.
2. Na Visão geral, confira o selo **Dados sintéticos · demonstração**.
3. Ajuste `eps`, `min_samples`, o raio geográfico e as variáveis selecionadas.
4. Execute a análise e explore clusters, ruído, perfis térmicos, grafo e componentes.
5. Abra **Dados e exportação** para importar CSV/GeoJSON ou baixar os resultados.
6. Abra **Análise** e selecione uma execução no histórico para recuperar seus parâmetros e resultados.
7. Reabra a aplicação para demonstrar que os conjuntos e o histórico continuam salvos no banco local.

## Arquitetura

```text
Navegador (HTML/CSS/JavaScript + Leaflet)
                │ HTTP / JSON / multipart
                ▼
        FastAPI (backend/app.py)
         ├── validação e importação (backend/processing.py)
         ├── DBSCAN, estatísticas e grafo Haversine
         └── SQLAlchemy ── SQLite (infraclima.db)
```

- `backend/app.py`: endpoints REST, upload, histórico, exportação e entrega do frontend.
- `backend/database.py`: configuração de SQLAlchemy e SQLite; `INFRACLIMA_DATABASE_URL` permite escolher outro arquivo SQLite. Conector e migração PostgreSQL/PostGIS não estão incluídos nesta versão.
- `backend/models.py`: entidades de conjuntos de dados, observações e análises, com chaves estrangeiras.
- `backend/processing.py`: leitura e validação CSV/GeoJSON, geração sintética e pipeline reproduzível.
- `backend/schemas.py`: validação dos parâmetros da API.
- `src/main.js`: navegação, apresentação dos resultados, estados de carregamento/erro e chamadas à API.
- `src/cluster.js`, `src/spatial-graph.js`, `src/statistics.js`: implementação original em JavaScript mantida para referência e testes do método anterior.
- `tests/`: validação do processamento e dos fluxos HTTP.

O banco é criado automaticamente em `infraclima.db` na primeira inicialização. Ele armazena metadados e observações dos conjuntos, assim como parâmetros, métricas e resultados de cada análise. Não há conta, serviço remoto ou sincronização entre computadores. O arquivo SQLite pode ser copiado como parte do material de demonstração. O uso de PostgreSQL/PostGIS exigirá instalar um driver e preparar uma migração de esquema.

## Método e interpretação

- A implementação backend preserva o DBSCAN do protótipo: as variáveis selecionadas (latitude, longitude e/ou temperatura) são padronizadas por Z-score e a distância do algoritmo é Euclidiana nesse espaço. Portanto, `eps` não é medido em quilômetros.
- O grafo é independente do DBSCAN. Ele conecta observações dentro do raio geográfico configurado e calcula distâncias com Haversine em quilômetros, além de grau e componentes conectados.
- A Silhouette exclui pontos de ruído, exige pelo menos dois grupos e não é calculada acima de 220 observações por custo quadrático.
- Agrupamentos indicam estrutura conforme os dados, variáveis e parâmetros escolhidos. Sozinhos, não comprovam ilha de calor, risco climático, causa ambiental ou degradação.
- LST (temperatura de superfície) e temperatura do ar são tipos diferentes e não são combinados automaticamente. A interface guarda o tipo declarado; cabe ao pesquisador documentar unidades, método, período, cobertura, resolução, fonte e licença.

## Importação de dados

O sistema aceita CSV e GeoJSON `FeatureCollection` com geometrias `Point`, coordenadas em WGS 84 e temperatura em °C. O limite é 3 MB e 800 pontos válidos. O importador aceita nomes comuns em português e inglês, permite mapear campos com cabeçalhos diferentes, valida faixas geográficas de coordenadas, valores térmicos finitos entre −100 e 100 °C e datas ISO ou brasileiras comuns, ignora linhas inválidas e duplicatas exatas e contabiliza cada categoria. Essa faixa térmica é uma verificação geral de entrada, não uma classificação climática. A unidade térmica exigida é °C: converta Kelvin antes da importação e registre a transformação. O sistema não reprojeta coordenadas nem verifica a fonte/licença dos arquivos.

Os campos Latitude, Longitude e Temperatura são detectados automaticamente quando usam nomes comuns. Se o arquivo usar outros cabeçalhos, os seletores apresentados após escolher o arquivo permitem mapeá-los antes de importar.

CSV mínimo:

```csv
id,latitude,longitude,temperatura_c
P1,-3.119,-60.022,34.8
P2,-3.118,-60.021,35.1
P3,-3.120,-60.023,34.6
```

GeoJSON usa a ordem normativa `[longitude, latitude]`:

```json
{
  "type": "FeatureCollection",
  "features": [
    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [-60.022, -3.119]}, "properties": {"id": "P1", "temperatura_c": 34.8}}
  ]
}
```

Conjuntos importados ficam separados do conjunto sintético. A fonte, o período, a licença, o tipo de temperatura e a resolução são metadados declarados pelo usuário, não certificados pelo sistema.

## API

Ao executar a aplicação, consulte Swagger em `/docs` ou OpenAPI em `/openapi.json`.

| Método | Endpoint | Uso |
|---|---|---|
| GET | `/api/health` | Estado da API e do banco |
| GET | `/api/datasets` | Listar conjuntos salvos |
| GET | `/api/datasets/{id}` | Metadados de um conjunto |
| POST | `/api/datasets/demo` | Criar ou recuperar a demonstração sintética |
| POST | `/api/datasets/import` | Importar arquivo e metadados via `multipart/form-data` |
| GET | `/api/datasets/{id}/observations` | Consultar observações persistidas |
| POST | `/api/analyses` | Executar DBSCAN e análise do grafo |
| GET | `/api/analyses/history` | Consultar execuções salvas |
| GET | `/api/analyses/{id}` | Recuperar uma execução completa |
| GET | `/api/analyses/{id}/export?format=geojson` | Exportar GeoJSON; também aceita `nodes`, `edges` e `summary` |
| GET | `/api/datasets/{id}/map` | Recuperar nós e metadados da análise mais recente |
| GET | `/api/datasets/{id}/graph` | Recuperar nós e arestas da análise mais recente |
| GET | `/api/datasets/{id}/stats` | Recuperar indicadores da análise mais recente |

## Testes

Com Python 3.10 ou superior e as dependências de desenvolvimento instaladas (`pip install -r requirements-dev.txt`):

```bash
python -m unittest discover -s tests -v
npm test
```

Os testes Python exercitam importação, descarte de inválidos/duplicados, distâncias Haversine, processamento sintético, endpoints, persistência de análise e exportação GeoJSON. Os testes JavaScript mantidos verificam o pipeline original do protótipo. Testes automatizados não substituem inspeção em diferentes navegadores, acessibilidade com usuários nem validação com dados reais.

## Estado e limitações da versão

Implementado: frontend existente e suas seis áreas; API local; banco SQLite; armazenamento de conjuntos, observações e histórico; geração sintética reprodutível; validação/importação CSV e GeoJSON; DBSCAN; grafo Haversine; métricas; recuperação do histórico; exportação CSV/GeoJSON; documentação OpenAPI.

Ainda necessário para uma avaliação científica: selecionar e documentar um conjunto real adequado a Manaus; verificar licença, unidade, período, cobertura e resolução; executar benchmarks e testes em Chrome/Firefox/Edge; validar usabilidade e acessibilidade; comparar os resultados com dados de referência e revisar a metodologia. Nesta primeira versão, o projeto não se conecta a provedores de dados externos nem a PostgreSQL/PostGIS.

## Roteiro curto para apresentação

Explique que a demonstração usa dados sintéticos; mostre a tela geral e os indicadores, altere parâmetros e execute o DBSCAN, abra um cluster e o grafo, importe um pequeno arquivo de amostra, exporte GeoJSON e recupere uma execução pelo histórico. Encerre explicando que a aplicação não classifica risco nem comprova ilhas de calor e que a próxima etapa científica é documentar e avaliar uma base real apropriada.

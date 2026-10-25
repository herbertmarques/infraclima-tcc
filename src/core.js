// Orquestração de aplicação; mantém UI desacoplada dos algoritmos.
import { standardize, dbscan, silhouette } from './cluster.js';
import { buildSpatialGraph } from './spatial-graph.js';
import { clusterProfiles, clusterAdjacency } from './statistics.js';
export { dbscan, silhouette } from './cluster.js';
export { haversineKm } from './spatial-graph.js';

export function demo(){let out=[],id=1;const groups=[[-3.119,-60.022,34.8],[-3.088,-60.015,39.2],[-3.145,-59.998,31.4]];for(let g=0;g<3;g++)for(let i=0;i<16;i++){let a=i%4,b=Math.floor(i/4),j=((i*7+g*3)%9-4)*.00125;out.push({id:`SIM-${String(id++).padStart(3,'0')}`,lat:groups[g][0]+(a-1.5)*.002+j*.25,lon:groups[g][1]+(b-1.5)*.002-j*.35,temp:+(groups[g][2]+((i*13+g*7)%11-5)*.42).toFixed(2)})}return out}

export function runAnalysis(raw,{eps,minPts,radius,features}){if(!raw.length)throw Error('Não há pontos para analisar.');if(!Number.isFinite(eps)||eps<=0||!Number.isInteger(minPts)||minPts<2||!Number.isFinite(radius)||radius<=0)throw Error('Parâmetros inválidos. ε e raio devem ser positivos; mínimo de pontos deve ser inteiro ≥ 2.');if(!features.length)throw Error('Selecione ao menos uma variável para o DBSCAN.');if(raw.length<minPts)throw Error(`Há ${raw.length} pontos; o mínimo configurado é ${minPts}.`);const z=Object.fromEntries(features.map(f=>[f,standardize(raw.map(n=>n[f]))])),prepared=raw.map((n,i)=>({...n,features:features.map(f=>z[f][i])})),labels=dbscan(prepared,eps,minPts),nodes=prepared.map((n,i)=>({...n,cluster:labels[i],degree:0,component:-1})),graph=buildSpatialGraph(nodes,radius);return{...graph,silhouette:silhouette(graph.nodes),profiles:clusterProfiles(graph.nodes),adjacency:clusterAdjacency(graph.nodes,graph.edges),params:{eps,minPts,radius,features:[...features]}}}

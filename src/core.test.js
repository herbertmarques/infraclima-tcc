import test from 'node:test';
import assert from 'node:assert/strict';
import { dbscan, haversineKm, runAnalysis, silhouette } from './core.js';
import { normalizeRows, parseCSV, parseSource } from './data-io.js';

test('Haversine returns zero for equal points and about 111 km per latitude degree',()=>{
  assert.equal(haversineKm({lat:-3,lon:-60},{lat:-3,lon:-60}),0);
  assert.ok(Math.abs(haversineKm({lat:0,lon:0},{lat:1,lon:0})-111.195)<0.2);
});

test('DBSCAN identifies two dense groups and a noise point',()=>{
  const data=[[-.1,0],[0,.1],[.1,0],[9.9,10],[10,9.9],[10.1,10],[30,30]].map((features)=>({features}));
  const labels=dbscan(data,.3,2);
  assert.equal(new Set(labels.filter(x=>x>=0)).size,2);
  assert.equal(labels.at(-1),-1);
  assert.equal(labels[0],labels[1]);
  assert.equal(labels[3],labels[4]);
});

test('pipeline attaches labels, degrees, components and thermal profiles',()=>{
  const raw=[{id:'A',lat:-3,lon:-60,temp:30},{id:'B',lat:-3,lon:-59.995,temp:30.2},{id:'C',lat:-3.1,lon:-60,temp:40},{id:'D',lat:-3.1,lon:-59.995,temp:40.2}];
  const result=runAnalysis(raw,{eps:1,minPts:2,radius:.7,features:['temp']});
  assert.equal(result.nodes.length,4);
  assert.equal(result.edges.length,2);
  assert.deepEqual(result.nodes.map(n=>n.degree),[1,1,1,1]);
  assert.equal(result.components,2);
  assert.equal(result.profiles.filter(p=>p.cluster>=0).length,2);
  assert.ok(result.nodes.every(n=>n.cluster>=0));
});

test('CSV parser accepts semicolon separators and decimal commas',()=>{
  const rows=parseCSV('id;latitude;longitude;temperatura_c\nP1;-3,1;-60,2;32,5\nP2;-3,2;-60,3;33,5\nP3;-3,3;-60,4;34,5');
  const data=normalizeRows(rows).out;
  assert.equal(data[0].lat,-3.1);
  assert.equal(data[0].temp,32.5);
});

test('GeoJSON import respects RFC coordinate order: longitude, latitude',()=>{
  const source=JSON.stringify({type:'FeatureCollection',features:[{type:'Feature',geometry:{type:'Point',coordinates:[-60.2,-3.1]},properties:{temperatura_c:31}},{type:'Feature',geometry:{type:'Point',coordinates:[-60.3,-3.2]},properties:{temperatura_c:32}},{type:'Feature',geometry:{type:'Point',coordinates:[-60.4,-3.3]},properties:{temperatura_c:33}}]});
  const data=normalizeRows(parseSource('amostra.geojson',source)).out;
  assert.equal(data[0].lon,-60.2);
  assert.equal(data[0].lat,-3.1);
});

test('normalizer removes exact duplicates and invalid coordinate/temperature rows',()=>{
  const input=[{id:'1',lat:'-3',lon:'-60',temp:'30'},{id:'2',lat:'-3',lon:'-60',temp:'30'},{id:'3',lat:'bad',lon:'-60',temp:'30'},{id:'4',lat:'-3',lon:'-60',temp:'31'},{id:'5',lat:'-3',lon:'-60',temp:'32'}];
  const {out,removed}=normalizeRows(input);
  assert.equal(out.length,3);
  assert.equal(removed,2);
});

test('Silhouette is unavailable when fewer than two non-noise groups remain',()=>{
  const sample=[{cluster:0,features:[0]},{cluster:0,features:[.1]},{cluster:-1,features:[9]}];
  assert.equal(silhouette(sample),null);
});

test('pipeline rejects invalid parameters instead of returning stale-looking results',()=>{
  assert.throws(()=>runAnalysis([{lat:0,lon:0,temp:25}],{eps:0,minPts:1,radius:-1,features:['temp']}),/Parâmetros inválidos/);
});

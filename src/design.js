/* Camada de apresentação: enriquece a interface sem alterar o pipeline. */
const paths = {
  overview:'<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
  map:'<path d="m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3Z"/><path d="M9 3v15M15 6v15"/>',
  graph:'<circle cx="5" cy="5" r="2.5"/><circle cx="19" cy="7" r="2.5"/><circle cx="8" cy="19" r="2.5"/><circle cx="19" cy="19" r="2.5"/><path d="m7.5 5.3 9 1.4M5.5 7.5 7.5 16.5M10.5 19h6M18.7 9.5v7M9.7 17.2l7.6-8"/>',
  analysis:'<path d="M4 3v18h17"/><path d="M8 16v-5M13 16V6M18 16V9"/>',
  data:'<path d="M12 3v12m-4-4 4 4 4-4"/><path d="M4 15v5a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-5"/>',
  about:'<path d="M4 4h6a3 3 0 0 1 3 3v14a4 4 0 0 0-4-2H4V4Z"/><path d="M13 7a3 3 0 0 1 3-3h5v15h-4a4 4 0 0 0-4 2"/>',
  play:'<path d="m9 5 10 7-10 7V5Z"/>',
  import:'<path d="M12 16V3m-4 4 4-4 4 4"/><path d="M4 14v6h16v-6"/>',
  arrow:'<path d="M5 12h14m-5-5 5 5-5 5"/>',
  reset:'<path d="M4 10a8 8 0 1 1 1 8"/><path d="M4 4v6h6"/>',
  tune:'<path d="M4 6h4m4 0h8M4 12h10m4 0h2M4 18h2m4 0h10"/><circle cx="10" cy="6" r="2"/><circle cx="16" cy="12" r="2"/><circle cx="8" cy="18" r="2"/>',
  info:'<circle cx="12" cy="12" r="9"/><path d="M12 10v7m0-11v1"/>',
  thermo:'<path d="M9 14V5a3 3 0 0 1 6 0v9a5 5 0 1 1-6 0Z"/><path d="M12 8v9"/><circle cx="12" cy="18" r="1.5"/>',
  noise:'<circle cx="5" cy="7" r="1.5"/><circle cx="11" cy="4" r="1.5"/><circle cx="17" cy="9" r="1.5"/><circle cx="8" cy="15" r="1.5"/><circle cx="18" cy="19" r="1.5"/><circle cx="3" cy="20" r="1.5"/>',
  pin:'<path d="M19 10c0 5-7 11-7 11S5 15 5 10a7 7 0 0 1 14 0Z"/><circle cx="12" cy="10" r="2.5"/>',
  menu:'<path d="M4 6h16M4 12h16M4 18h16"/>',
  close:'<path d="m6 6 12 12M18 6 6 18"/>',
  brand:'<path d="M3 18h4l4-12 4 12h6"/><circle cx="11" cy="6" r="2"/><circle cx="7" cy="18" r="2"/><circle cx="15" cy="18" r="2"/>'
};
function icon(name) { return '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">'+(paths[name]||paths.info)+'</svg>'; }
function prependIcon(element,name) { if(element && !element.querySelector('.icon')) element.insertAdjacentHTML('afterbegin',icon(name)); }

function layoutGraphLabels(svg) {
  svg.querySelectorAll('.node-label-leader').forEach(line=>line.remove());
  const groups=[...svg.querySelectorAll('g[data-node]')];
  const nodes=groups.map(group=>{const circle=group.querySelector('circle');return{x:+circle.getAttribute('cx'),y:+circle.getAttribute('cy'),r:+circle.getAttribute('r')};});
  const placed=[],directions=[[1,-1],[-1,-1],[1,1],[-1,1],[1,0],[-1,0],[0,-1],[0,1]];
  const overlaps=(a,b)=>a.x<b.x+b.w&&a.x+a.w>b.x&&a.y<b.y+b.h&&a.y+a.h>b.y;
  groups.forEach((group,index)=>{
    const text=group.querySelector('text'),node=nodes[index],width=text.getComputedTextLength()||text.textContent.length*6,height=13;
    let chosen;
    for(let ring=0;ring<14&&!chosen;ring++)for(const [dx,dy] of directions){
      const x=node.x+dx*(14+ring*12)-(dx<0?width:dx===0?width/2:0);
      const y=node.y+dy*(14+ring*10)+(dy===0?4:0);
      const box={x:x-2,y:y-10,w:width+4,h:height};
      if(box.x<7||box.x+box.w>893||box.y<7||box.y+box.h>553)continue;
      if(placed.some(other=>overlaps(box,other)))continue;
      if(nodes.some(other=>overlaps(box,{x:other.x-other.r-2,y:other.y-other.r-2,w:other.r*2+4,h:other.r*2+4})))continue;
      chosen={x,y,box};break;
    }
    if(!chosen){chosen={x:+text.getAttribute('x'),y:+text.getAttribute('y')};chosen.box={x:chosen.x,y:chosen.y-10,w:width,h:height};}
    placed.push(chosen.box);text.setAttribute('x',chosen.x);text.setAttribute('y',chosen.y);
    text.setAttribute('paint-order','stroke');text.setAttribute('stroke','#fbfdfb');text.setAttribute('stroke-width','3');text.setAttribute('stroke-linejoin','round');
    const endX=Math.max(chosen.x,Math.min(node.x,chosen.x+width)),endY=Math.max(chosen.y-8,Math.min(node.y,chosen.y+2)),dist=Math.hypot(endX-node.x,endY-node.y);
    if(dist>node.r+12){const leader=document.createElementNS('http://www.w3.org/2000/svg','line');leader.setAttribute('x1',node.x);leader.setAttribute('y1',node.y);leader.setAttribute('x2',endX);leader.setAttribute('y2',endY);leader.setAttribute('class','node-label-leader');leader.setAttribute('aria-hidden','true');group.insertBefore(leader,text);}
  });
}

function initDesign() {
  const sidebar=document.getElementById('sidebar'),menu=document.getElementById('menu');
  document.querySelector('main').id='main-content';
  document.querySelector('main').setAttribute('tabindex','-1');
  const skip=document.createElement('a');skip.className='skip-link';skip.href='#main-content';skip.textContent='Ir para o conteúdo';document.body.prepend(skip);
  document.querySelector('.mark').innerHTML=icon('brand');
  const nav=document.querySelector('.nav');
  const navHeading=document.createElement('div');navHeading.className='nav-heading';navHeading.textContent='Espaço de análise';nav.prepend(navHeading);
  document.querySelectorAll('.nav button').forEach(button=>{
    button.querySelector('.ico').innerHTML=icon(button.dataset.view);
    button.querySelector('.ico').setAttribute('aria-hidden','true');
  });
  prependIcon(document.querySelector('.side-note b'),'info');
  menu.innerHTML=icon('menu');menu.setAttribute('aria-controls','sidebar');menu.setAttribute('aria-expanded','false');
  const close=document.createElement('button');close.className='nav-close';close.type='button';close.setAttribute('aria-label','Fechar menu');close.innerHTML=icon('close');sidebar.prepend(close);
  const scrim=document.createElement('button');scrim.className='mobile-scrim';scrim.type='button';scrim.setAttribute('aria-label','Fechar menu de navegação');scrim.setAttribute('tabindex','-1');document.body.append(scrim);
  const mobile=window.matchMedia('(max-width:760px)');
  function syncMenu() {
    const open=mobile.matches && sidebar.classList.contains('open');
    scrim.classList.toggle('show',open);
    document.body.classList.toggle('menu-open',open);
    menu.setAttribute('aria-expanded',String(open));
    sidebar.inert=mobile.matches&&!open;
    if(mobile.matches&&!open) sidebar.setAttribute('aria-hidden','true');else sidebar.removeAttribute('aria-hidden');
  }
  function closeMenu(){sidebar.classList.remove('open');syncMenu();menu.focus();}
  close.addEventListener('click',closeMenu);scrim.addEventListener('click',closeMenu);
  menu.addEventListener('click',()=>{syncMenu();if(sidebar.classList.contains('open'))sidebar.querySelector('.nav button.active').focus();});
  new MutationObserver(syncMenu).observe(sidebar,{attributes:true,attributeFilter:['class']});
  mobile.addEventListener('change',()=>{sidebar.classList.remove('open');syncMenu();});
  document.querySelectorAll('.nav button').forEach(button=>button.addEventListener('click',()=>{
    if(mobile.matches){const title=document.querySelector('.view.active h1');title.tabIndex=-1;title.focus({preventScroll:true});}
  }));
  document.addEventListener('keydown',event=>{
    if(!mobile.matches||!sidebar.classList.contains('open'))return;
    if(event.key==='Escape'){event.preventDefault();closeMenu();}
    if(event.key==='Tab'){
      const items=[...sidebar.querySelectorAll('button:not([disabled])')],first=items[0],last=items.at(-1);
      if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}
      else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}
    }
  });
  syncMenu();

  const notice=document.querySelector('.notice');
  const copy=document.createElement('span');copy.className='notice-copy';
  while(notice.firstChild)copy.append(notice.firstChild);
  notice.append(copy);notice.insertAdjacentHTML('afterbegin',icon('info'));notice.setAttribute('role','note');
  let currentView;
  function syncView(){
    const active=document.querySelector('.view.active'),head=active?.querySelector('.page-head');
    if(active!==currentView){currentView=active;window.scrollTo({top:0,left:0,behavior:'instant'});if(active?.id==='view-graph')requestAnimationFrame(()=>layoutGraphLabels(document.getElementById('graphSvg')));}
    if(head&&head.nextElementSibling!==notice)head.after(notice);
    document.querySelectorAll('.nav button').forEach(button=>{
      if(button.classList.contains('active'))button.setAttribute('aria-current','page');else button.removeAttribute('aria-current');
    });
  }
  document.querySelectorAll('.view').forEach(view=>new MutationObserver(syncView).observe(view,{attributes:true,attributeFilter:['class']}));
  syncView();
  const hero=document.querySelector('#view-overview .page-head');
  const motif=document.createElement('span');motif.className='hero-motif';motif.setAttribute('aria-hidden','true');
  motif.innerHTML='<svg viewBox="0 0 260 190" fill="none"><g stroke="currentColor" stroke-width="1"><path d="m12 130 60-90 66 38 90-45M12 130l116 35 10-87 90 37-100 50M72 40l-8 96 74-58m90 37V33M64 136l64 29"/></g><g fill="currentColor"><circle cx="12" cy="130" r="4"/><circle cx="72" cy="40" r="5"/><circle cx="138" cy="78" r="6"/><circle cx="228" cy="33" r="4"/><circle cx="228" cy="115" r="5"/><circle cx="128" cy="165" r="5"/><circle cx="64" cy="136" r="3"/></g></svg>';
  hero.append(motif);
  const experiment=document.querySelector('#view-overview .layout>.panel:last-child');
  experiment.classList.add('experiment-panel');experiment.id='experiment-panel';
  prependIcon(experiment.querySelector('h2'),'tune');
  const label=document.createElement('p');label.className='section-label';label.textContent='Variáveis de agrupamento';experiment.querySelector('.checkrow').before(label);
  const help=experiment.querySelector('.footnote');help.id='parameter-help';
  ['eps','minPts','radius'].forEach(id=>document.getElementById(id).setAttribute('aria-describedby','parameter-help'));
  document.querySelector('#view-overview>.panel').classList.add('profile-panel');
  const uploadHelp=document.querySelector('.upload .footnote');uploadHelp.id='upload-help';
  document.getElementById('fileInput').setAttribute('aria-describedby','upload-help');
  const graph=document.getElementById('graphSvg');graph.setAttribute('role','group');
  const graphCanvas=document.createElement('div');graphCanvas.className='graph-canvas-wrap';graphCanvas.tabIndex=0;graphCanvas.setAttribute('role','region');graphCanvas.setAttribute('aria-label','Grafo espacial com rolagem em telas pequenas');graph.before(graphCanvas);graphCanvas.append(graph);
  const graphHint=document.createElement('p');graphHint.className='graph-scroll-hint';graphHint.textContent='Em telas pequenas, deslize horizontalmente para explorar o grafo.';graphCanvas.after(graphHint);
  layoutGraphLabels(graph);new MutationObserver(()=>layoutGraphLabels(graph)).observe(graph,{childList:true});
  document.getElementById('graphSummary').setAttribute('aria-live','polite');
  document.querySelectorAll('.map').forEach(map=>{
    const wrap=map.parentElement;
    function tileWarning(){
      if(wrap.querySelector('.map-network-status'))return;
      const warning=document.createElement('div');warning.className='map-network-status';warning.setAttribute('role','status');
      warning.textContent='Alguns blocos do mapa não carregaram. As observações continuam disponíveis.';wrap.append(warning);
    }
    map.addEventListener('error',event=>{if(event.target.matches?.('img.leaflet-tile'))tileWarning();},true);
    if([...map.querySelectorAll('img.leaflet-tile')].some(img=>img.complete&&img.naturalWidth===0))tileWarning();
  });
  document.querySelectorAll('.table-wrap').forEach(table=>{
    table.tabIndex=0;table.setAttribute('role','region');
    table.setAttribute('aria-label',table.closest('.panel')?.querySelector('h2,h3')?.textContent.trim()||'Tabela de resultados');
  });
  document.querySelectorAll('.btn').forEach(button=>{
    const name=button.classList.contains('run')?'play':button.dataset.go==='data'?'import':button.dataset.go==='map'?'arrow':button.id==='loadFile'?'import':button.id==='restoreDemo'?'reset':'data';
    prependIcon(button,name);
  });
  function decorateMetrics(target){
    target.querySelectorAll('.metric').forEach((metric,index)=>{
      if(metric.querySelector('.metric-icon'))return;
      const label=metric.querySelector('small')?.textContent||'';
      const type=label.includes('Temperatura')?'thermo':label.includes('ruído')?'noise':label.includes('Agrup')?'graph':label.includes('Observa')?'pin':['analysis','graph','graph','map','tune'][index%5];
      const slot=document.createElement('span');slot.className='metric-icon';slot.innerHTML=icon(type);slot.setAttribute('aria-hidden','true');metric.prepend(slot);
    });
  }
  ['metrics','analysisMetrics'].forEach(id=>{
    const target=document.getElementById(id);decorateMetrics(target);
    new MutationObserver(()=>decorateMetrics(target)).observe(target,{childList:true});
  });
  const status=document.getElementById('runStatus');
  function styleStatus(){
    status.dataset.state=status.textContent.startsWith('Análise concluída')?'success':'error';
    status.classList.remove('updated');void status.offsetWidth;status.classList.add('updated');
  }
  styleStatus();new MutationObserver(styleStatus).observe(status,{childList:true});
  const importButton=document.getElementById('loadFile'),message=document.getElementById('importMessage');
  importButton.addEventListener('click',()=>importButton.setAttribute('aria-busy','true'),{capture:true});
  new MutationObserver(()=>importButton.removeAttribute('aria-busy')).observe(message,{childList:true});
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',initDesign,{once:true});else initDesign();

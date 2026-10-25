// Gera uma página informativa: a aplicação completa requer o backend FastAPI.
import { writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = dirname(fileURLToPath(import.meta.url));
const html = `<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#102b34"><title>InfraClima — iniciar aplicação</title>
<style>
*{box-sizing:border-box}body{margin:0;min-height:100vh;display:grid;place-items:center;padding:24px;background:#f2f7f5;color:#19363a;font:16px/1.6 system-ui,sans-serif}.card{max-width:680px;padding:40px;background:#fff;border:1px solid #dbe7e2;border-radius:22px;box-shadow:0 20px 60px #16362b12}h1{margin:.2em 0;font-size:clamp(2rem,6vw,3.2rem);letter-spacing:-.04em}p{color:#50686a}.mark{display:grid;place-items:center;width:48px;height:48px;border-radius:15px;background:#e2f3eb;color:#13765f;font-size:28px}.button{display:inline-block;margin:12px 0;padding:12px 18px;border-radius:10px;background:#087e68;color:white;text-decoration:none;font-weight:700}.note{padding:14px 16px;border-left:4px solid #db9f32;background:#fff8e8;border-radius:6px;color:#684b12}code{padding:2px 5px;border-radius:4px;background:#edf2ef}ol{padding-left:22px;color:#365154}
</style></head><body><main class="card"><div class="mark" aria-hidden="true">∿</div><h1>InfraClima</h1><p>O sistema completo agora usa uma API local e um banco SQLite para processar e salvar os dados. Esta página única é apenas um guia de inicialização.</p><ol><li>Na pasta do projeto, execute <code>iniciar_infraclima.bat</code> no Windows ou <code>iniciar_infraclima.sh</code> no Linux/macOS.</li><li>O script prepara as dependências na primeira execução e inicia o servidor local.</li><li>Abra a aplicação no endereço local informado pelo script.</li></ol><a class="button" href="http://127.0.0.1:8000">Abrir InfraClima local</a><p class="note"><strong>Dados de demonstração são sintéticos.</strong> Não representam medições reais. O mapa de fundo precisa de internet; as análises, tabelas, grafo e exportações são processados localmente.</p></main></body></html>`;
const output = join(root, 'Visualizar_InfraClima.html');
writeFileSync(output, html);
console.log(output);

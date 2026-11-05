// Construye dist/app.js (script clásico IIFE, funciona también abriendo index.html con file://)
// y dist/datos.js (GLB en base64 + geometría), para que el visor no dependa de fetch.
//
// Requisitos: three 0.180.0 resoluble como paquete "three" (p. ej. `npm i --no-save three@0.180.0`
// en la raíz del repositorio) y esbuild (`npx esbuild` o variable ESBUILD con su ruta).
//   node apartamento-102/tools/build.mjs
import { execFileSync } from 'node:child_process';
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
mkdirSync(join(root, 'dist'), { recursive: true });

const glb = readFileSync(join(root, 'modelo/apto-102-propuesta.glb')).toString('base64');
const geo = JSON.parse(readFileSync(join(root, 'data/propuesta-102.json'), 'utf8'));
delete geo.original.rotulos;
// propuesta de balcón (no figura en el DWG): se embebe aparte para que el visor la rotule como tal
const propuesta = geo.balcon;
writeFileSync(join(root, 'dist/datos.js'),
  '/* Generado por tools/build.mjs: modelo GLB y propuesta de redistribución del apartamento 102 (rediseño conceptual). */\n' +
  `window.APTO102=${JSON.stringify({ glb, geo, propuesta })};\n`);

const esbuild = process.env.ESBUILD || 'esbuild';
execFileSync(esbuild, [join(root, 'src/app.mjs'), '--bundle', '--format=iife', '--target=es2020', '--minify',
  '--legal-comments=eof', `--outfile=${join(root, 'dist/app.js')}`],
  { stdio: 'inherit', env: { ...process.env } });
console.log('dist/app.js y dist/datos.js listos');

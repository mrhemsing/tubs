#!/usr/bin/env node
/** SeedVR upscale smoke test.
 * Uses fal-ai/seedvr/upscale/image with factor mode + 4.0x scale.
 * Outputs a tiny comparison set under public/seedvr-test/ without touching review UI.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import { File } from 'node:buffer';
import { fal } from '@fal-ai/client';

const ROOT = process.cwd();
const PUBLIC = path.join(ROOT, 'public');
const OUT_DIR = path.join(PUBLIC, 'seedvr-test');
const OUT_INDEX = path.join(PUBLIC, 'seedvr-test.json');
const ENDPOINT = 'fal-ai/seedvr/upscale/image';

const args = new Map();
for (let i = 2; i < process.argv.length; i += 1) {
  const part = process.argv[i];
  if (part.startsWith('--')) {
    const [k, inline] = part.split('=');
    args.set(k, inline ?? process.argv[i + 1] ?? '');
    if (inline === undefined && process.argv[i + 1] && !process.argv[i + 1].startsWith('--')) i += 1;
  }
}
const limit = Number(args.get('--limit') || 5);
const upscaleFactor = Number(args.get('--scale') || 4.0);
const noiseScale = Number(args.get('--noise-scale') || 0.1);
const outputFormat = args.get('--output-format') || 'jpg';

if (!process.env.FAL_KEY) {
  console.error('Missing FAL_KEY. Set it only for this command; do not commit it.');
  process.exit(1);
}
fal.config({ credentials: process.env.FAL_KEY });

function localPath(url) {
  return path.join(PUBLIC, String(url || '').replace(/^\//, '').replaceAll('/', path.sep));
}
function outName(url) {
  const parsed = path.parse(String(url).replace(/^\//, ''));
  return `${parsed.name}-seedvr-${upscaleFactor}x.${outputFormat === 'png' ? 'png' : 'jpg'}`;
}
async function exists(file) {
  try { await fs.access(file); return true; } catch { return false; }
}
async function upload(filePath) {
  const buf = await fs.readFile(filePath);
  const file = new File([buf], path.basename(filePath), { type: filePath.toLowerCase().endsWith('.png') ? 'image/png' : 'image/jpeg' });
  return fal.storage.upload(file);
}
async function download(url, dest) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`download failed ${res.status} ${url}`);
  await fs.writeFile(dest, Buffer.from(await res.arrayBuffer()));
}
function collectTargets(review, tub) {
  const targets = [];
  const add = (kind, listingId, address, url) => {
    if (!url) return;
    targets.push({ kind, listingId, address, url, src: localPath(url), out: `/seedvr-test/${outName(url)}` });
  };
  for (const card of review.cards || []) {
    add('primary', card.listingId, card.address, card.thumbs?.[0]?.url);
    if (targets.length >= Math.ceil(limit / 2)) break;
  }
  for (const item of tub.mockups || []) {
    add('tub', item.listingId, item.address, item.mockup);
    if (targets.length >= limit) break;
  }
  return targets.slice(0, limit);
}

async function main() {
  await fs.mkdir(OUT_DIR, { recursive: true });
  const review = JSON.parse(await fs.readFile(path.join(PUBLIC, 'review-data.json'), 'utf8'));
  const tub = JSON.parse(await fs.readFile(path.join(PUBLIC, 'tub-mockups.json'), 'utf8'));
  const targets = collectTargets(review, tub);
  const rows = [];

  console.log(`SeedVR test: ${targets.length} images, standard/factor mode, scale=${upscaleFactor}x, noise=${noiseScale}`);
  for (const [index, target] of targets.entries()) {
    if (!(await exists(target.src))) {
      console.warn(`missing source ${target.url}`);
      continue;
    }
    const dest = path.join(PUBLIC, target.out.replace(/^\//, '').replaceAll('/', path.sep));
    console.log(`[${index + 1}/${targets.length}] ${target.kind} ${target.address}`);
    const imageUrl = await upload(target.src);
    const result = await fal.subscribe(ENDPOINT, {
      input: {
        image_url: imageUrl,
        upscale_mode: 'factor',
        upscale_factor: upscaleFactor,
        noise_scale: noiseScale,
        output_format: outputFormat,
      },
      logs: false,
    });
    const image = result?.data?.image || result?.image;
    if (!image?.url) throw new Error(`No image URL returned: ${JSON.stringify(result).slice(0, 500)}`);
    await download(image.url, dest);
    rows.push({ ...target, upscaled: target.out, endpoint: ENDPOINT, upscale_mode: 'factor', upscale_factor: upscaleFactor, noise_scale: noiseScale, output_format: outputFormat, width: image.width, height: image.height });
  }
  await fs.writeFile(OUT_INDEX, JSON.stringify({ generatedAt: new Date().toISOString(), count: rows.length, endpoint: ENDPOINT, upscale_mode: 'factor', upscale_factor: upscaleFactor, noise_scale: noiseScale, output_format: outputFormat, images: rows }, null, 2));
  console.log(`Wrote ${path.relative(ROOT, OUT_INDEX)} (${rows.length} entries)`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});

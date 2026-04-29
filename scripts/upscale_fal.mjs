#!/usr/bin/env node
/** Upscale selected review images via FAL/RealESRGAN.
 *
 * Requires FAL_KEY in env. Outputs to public/upscaled-4x/ and writes
 * public/upscaled-4x.json. Originals are never overwritten.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import { File } from 'node:buffer';
import { fal } from '@fal-ai/client';

const ROOT = process.cwd();
const PUBLIC = path.join(ROOT, 'public');
const REVIEW_DATA = path.join(PUBLIC, 'review-data.json');
const TUB_DATA = path.join(PUBLIC, 'tub-mockups.json');
const OUT_DIR = path.join(PUBLIC, 'upscaled-4x');
const OUT_INDEX = path.join(PUBLIC, 'upscaled-4x.json');

const args = new Map();
for (let i = 2; i < process.argv.length; i += 1) {
  const part = process.argv[i];
  if (part.startsWith('--')) {
    const [k, inline] = part.split('=');
    args.set(k, inline ?? process.argv[i + 1] ?? '');
    if (inline === undefined && process.argv[i + 1] && !process.argv[i + 1].startsWith('--')) i += 1;
  }
}
const mode = args.get('--mode') || 'primary-and-tub';
const limit = Number(args.get('--limit') || 0);
const endpoint = args.get('--endpoint') || 'fal-ai/esrgan';
const model = args.get('--model') || 'RealESRGAN_x4plus';
const scale = Number(args.get('--scale') || 4);
const concurrency = Math.max(1, Number(args.get('--concurrency') || 4));

if (!process.env.FAL_KEY) {
  console.error('Missing FAL_KEY. Set FAL_KEY for this command only; do not commit it.');
  process.exit(1);
}
fal.config({ credentials: process.env.FAL_KEY });

function localPath(url) {
  return path.join(PUBLIC, String(url || '').replace(/^\//, '').replaceAll('/', path.sep));
}

function outName(url) {
  const parsed = path.parse(String(url).replace(/^\//, ''));
  return `${parsed.name}-4x.jpg`;
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
  const ab = await res.arrayBuffer();
  const tmp = `${dest}.download`;
  await fs.writeFile(tmp, Buffer.from(ab));
  // Convert provider output to optimized JPEG. FAL/ESRGAN often returns PNGs
  // that are far too large for a static review site.
  const sharp = await import('sharp');
  await sharp.default(tmp).jpeg({ quality: 88, progressive: true, mozjpeg: true }).toFile(dest);
  await fs.unlink(tmp).catch(() => {});
}

function collectTargets(review, tub) {
  const targets = [];
  const add = (kind, listingId, address, url) => {
    if (!url) return;
    const src = localPath(url);
    targets.push({ kind, listingId, address, url, src, out: `/upscaled-4x/${outName(url)}` });
  };

  if (mode === 'primary' || mode === 'primary-and-tub' || mode === 'all-card-visible') {
    for (const card of review.cards || []) {
      add('primary', card.listingId, card.address, card.thumbs?.[0]?.url);
      if (mode === 'all-card-visible') {
        for (const thumb of card.thumbs?.slice(1) || []) add('thumb', card.listingId, card.address, thumb.url);
      }
    }
  }
  if ((mode === 'tub' || mode === 'primary-and-tub' || mode === 'all-card-visible') && tub) {
    for (const item of tub.mockups || []) add('tub', item.listingId, item.address, item.mockup);
  }

  const seen = new Set();
  return targets.filter((target) => {
    if (seen.has(target.url)) return false;
    seen.add(target.url);
    return true;
  });
}

async function writeIndex(byUrl) {
  const images = [...byUrl.values()].sort((a, b) => `${a.kind}:${a.address}`.localeCompare(`${b.kind}:${b.address}`));
  await fs.writeFile(OUT_INDEX, JSON.stringify({ generatedAt: new Date().toISOString(), count: images.length, images }, null, 2));
  return images.length;
}

async function main() {
  const review = JSON.parse(await fs.readFile(REVIEW_DATA, 'utf8'));
  const tub = await exists(TUB_DATA) ? JSON.parse(await fs.readFile(TUB_DATA, 'utf8')) : null;
  await fs.mkdir(OUT_DIR, { recursive: true });
  const previous = await exists(OUT_INDEX) ? JSON.parse(await fs.readFile(OUT_INDEX, 'utf8')) : { images: [] };
  const byUrl = new Map((previous.images || []).map((item) => [item.url, item]));

  let targets = collectTargets(review, tub);
  if (limit) targets = targets.slice(0, limit);
  console.log(`Upscaling ${targets.length} images via ${endpoint} (${model}, ${scale}x), concurrency=${concurrency}`);

  let cursor = 0;
  let completed = 0;
  async function processTarget(target, index) {
    const dest = path.join(PUBLIC, target.out.replace(/^\//, '').replaceAll('/', path.sep));
    if (await exists(dest)) {
      byUrl.set(target.url, { ...target, upscaled: target.out, skipped: true });
      completed += 1;
      return;
    }
    if (!(await exists(target.src))) {
      console.warn(`missing local source: ${target.url}`);
      completed += 1;
      return;
    }
    console.log(`[${index + 1}/${targets.length}] ${target.kind} ${target.address}`);
    const imageUrl = await upload(target.src);
    const result = await fal.subscribe(endpoint, {
      input: { image_url: imageUrl, scale, model },
      logs: false,
    });
    const image = result?.data?.image || result?.image || result?.data?.images?.[0] || result?.images?.[0];
    const upUrl = image?.url;
    if (!upUrl) throw new Error(`No image URL returned for ${target.url}: ${JSON.stringify(result).slice(0, 500)}`);
    await download(upUrl, dest);
    byUrl.set(target.url, { ...target, upscaled: target.out, endpoint, model, scale });
    completed += 1;
    if (completed % 5 === 0) await writeIndex(byUrl);
  }

  async function worker() {
    while (cursor < targets.length) {
      const index = cursor++;
      await processTarget(targets[index], index);
    }
  }

  await Promise.all(Array.from({ length: Math.min(concurrency, targets.length) }, () => worker()));
  const count = await writeIndex(byUrl);
  console.log(`Wrote ${path.relative(ROOT, OUT_INDEX)} (${count} entries)`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});

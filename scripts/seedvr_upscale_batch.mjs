#!/usr/bin/env node
/** Batch upscale review images with SeedVR.
 *
 * Uses fal-ai/seedvr/upscale/image in factor mode at 4.0x by default.
 * Outputs to public/seedvr-4x/ and public/seedvr-4x.json.
 * Originals are never overwritten; the review UI can opt in after QA.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import { File } from 'node:buffer';
import { fal } from '@fal-ai/client';

const ROOT = process.cwd();
const PUBLIC = path.join(ROOT, 'public');
const OUT_DIR = path.join(PUBLIC, 'seedvr-4x');
const OUT_INDEX = path.join(PUBLIC, 'seedvr-4x.json');
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
const mode = args.get('--mode') || 'primary-tub-design-base';
const limit = Number(args.get('--limit') || 0);
const concurrency = Math.max(1, Number(args.get('--concurrency') || 4));
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
  const tmp = `${dest}.download`;
  await fs.writeFile(tmp, Buffer.from(await res.arrayBuffer()));
  await fs.rename(tmp, dest);
}
function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
function addTarget(targets, kind, listingId, address, url) {
  if (!url) return;
  targets.push({ kind, listingId, address, url, src: localPath(url), upscaled: `/seedvr-4x/${outName(url)}` });
}
function collectTargets(review, tub) {
  const targets = [];
  if (['primary', 'primary-and-tub', 'primary-tub-design-base', 'all'].includes(mode)) {
    for (const card of review.cards || []) addTarget(targets, 'primary', card.listingId, card.address, card.thumbs?.[0]?.url);
  }
  if (['tub', 'primary-and-tub', 'primary-tub-design-base', 'all'].includes(mode)) {
    for (const item of tub.mockups || []) addTarget(targets, 'tub', item.listingId, item.address, item.mockup);
  }
  if (['design-base', 'primary-tub-design-base', 'all'].includes(mode)) {
    for (const item of tub.mockups || []) addTarget(targets, 'design-base', item.listingId, item.address, item.sourceImage);
  }
  const seen = new Set();
  const unique = targets.filter((target) => {
    if (seen.has(target.url)) return false;
    seen.add(target.url);
    return true;
  });
  return limit ? unique.slice(0, limit) : unique;
}
async function writeIndex(byUrl) {
  const images = [...byUrl.values()].sort((a, b) => `${a.kind}:${a.address}`.localeCompare(`${b.kind}:${b.address}`));
  await fs.writeFile(OUT_INDEX, JSON.stringify({
    generatedAt: new Date().toISOString(),
    count: images.length,
    endpoint: ENDPOINT,
    upscale_mode: 'factor',
    upscale_factor: upscaleFactor,
    noise_scale: noiseScale,
    output_format: outputFormat,
    images,
  }, null, 2));
  return images.length;
}

async function main() {
  await fs.mkdir(OUT_DIR, { recursive: true });
  const review = JSON.parse(await fs.readFile(path.join(PUBLIC, 'review-data.json'), 'utf8'));
  const tub = JSON.parse(await fs.readFile(path.join(PUBLIC, 'tub-mockups.json'), 'utf8'));
  const previous = await exists(OUT_INDEX) ? JSON.parse(await fs.readFile(OUT_INDEX, 'utf8')) : { images: [] };
  const byUrl = new Map((previous.images || []).map((item) => [item.url, item]));
  const targets = collectTargets(review, tub);
  console.log(`SeedVR batch: ${targets.length} unique images, mode=${mode}, scale=${upscaleFactor}x, concurrency=${concurrency}`);

  let cursor = 0;
  let completed = 0;
  async function processTarget(target, index) {
    const dest = path.join(PUBLIC, target.upscaled.replace(/^\//, '').replaceAll('/', path.sep));
    if (await exists(dest)) {
      byUrl.set(target.url, { ...target, endpoint: ENDPOINT, upscale_mode: 'factor', upscale_factor: upscaleFactor, noise_scale: noiseScale, output_format: outputFormat, skipped: true });
      completed += 1;
      return;
    }
    if (!(await exists(target.src))) {
      console.warn(`missing source: ${target.url}`);
      completed += 1;
      return;
    }
    console.log(`[${index + 1}/${targets.length}] ${target.kind} ${target.address}`);
    let lastError;
    for (let attempt = 1; attempt <= 3; attempt += 1) {
      try {
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
        byUrl.set(target.url, { ...target, endpoint: ENDPOINT, upscale_mode: 'factor', upscale_factor: upscaleFactor, noise_scale: noiseScale, output_format: outputFormat, width: image.width, height: image.height });
        lastError = null;
        break;
      } catch (err) {
        lastError = err;
        console.warn(`retry ${attempt}/3 failed for ${target.url}: ${err.message}`);
        await delay(2000 * attempt);
      }
    }
    if (lastError) throw lastError;
    completed += 1;
    if (completed % 10 === 0) await writeIndex(byUrl);
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

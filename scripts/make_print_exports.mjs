#!/usr/bin/env node
/** Create conservative print-ready exports without AI hallucination.
 *
 * This uses regular resampling + light sharpening only. It does not invent
 * detail, so aerials keep their real/photographic look for print layouts.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import sharp from 'sharp';

const ROOT = process.cwd();
const PUBLIC = path.join(ROOT, 'public');
const OUT_DIR = path.join(PUBLIC, 'print-ready');
const OUT_INDEX = path.join(PUBLIC, 'print-ready.json');

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
const width = Number(args.get('--width') || 2400);
const quality = Number(args.get('--quality') || 92);

function localPath(url) {
  return path.join(PUBLIC, String(url || '').replace(/^\//, '').replaceAll('/', path.sep));
}

function outName(url) {
  const parsed = path.parse(String(url).replace(/^\//, ''));
  return `${parsed.name}-print.jpg`;
}

async function exists(file) {
  try { await fs.access(file); return true; } catch { return false; }
}

function addTarget(targets, kind, listingId, address, url) {
  if (!url) return;
  targets.push({ kind, listingId, address, url, src: localPath(url), print: `/print-ready/${outName(url)}` });
}

async function main() {
  await fs.mkdir(OUT_DIR, { recursive: true });
  const review = JSON.parse(await fs.readFile(path.join(PUBLIC, 'review-data.json'), 'utf8'));
  const tubPath = path.join(PUBLIC, 'tub-mockups.json');
  const tub = await exists(tubPath) ? JSON.parse(await fs.readFile(tubPath, 'utf8')) : { mockups: [] };

  const targets = [];
  if (mode === 'primary' || mode === 'primary-and-tub') {
    for (const card of review.cards || []) addTarget(targets, 'primary', card.listingId, card.address, card.thumbs?.[0]?.url);
  }
  if (mode === 'tub' || mode === 'primary-and-tub') {
    for (const item of tub.mockups || []) addTarget(targets, 'tub', item.listingId, item.address, item.mockup);
  }

  const seen = new Set();
  const unique = targets.filter((target) => {
    if (seen.has(target.url)) return false;
    seen.add(target.url);
    return true;
  });

  const rows = [];
  for (const [index, target] of unique.entries()) {
    if (!(await exists(target.src))) {
      console.warn(`missing source: ${target.url}`);
      continue;
    }
    const dest = path.join(PUBLIC, target.print.replace(/^\//, '').replaceAll('/', path.sep));
    const meta = await sharp(target.src).metadata();
    const targetWidth = Math.max(meta.width || width, width);
    await sharp(target.src)
      .resize({ width: targetWidth, withoutEnlargement: false, kernel: sharp.kernel.lanczos3 })
      .sharpen({ sigma: 0.6, m1: 0.4, m2: 1.2 })
      .jpeg({ quality, progressive: true, mozjpeg: true })
      .toFile(dest);
    rows.push({ ...target, originalWidth: meta.width, originalHeight: meta.height, printWidth: targetWidth, method: 'lanczos3_light_sharpen_no_ai' });
    if ((index + 1) % 50 === 0) console.log(`processed ${index + 1}/${unique.length}`);
  }

  await fs.writeFile(OUT_INDEX, JSON.stringify({ generatedAt: new Date().toISOString(), count: rows.length, width, quality, method: 'non_ai_lanczos3_light_sharpen', images: rows }, null, 2));
  console.log(`Wrote ${path.relative(ROOT, OUT_INDEX)} (${rows.length} entries)`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});

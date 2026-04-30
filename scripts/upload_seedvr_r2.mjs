import crypto from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';

const ROOT = process.cwd();
const SOURCE_DIR = path.join(ROOT, 'public', 'seedvr-4x');

function requireEnv(name) {
  const value = process.env[name];
  if (!value) throw new Error(`Missing required env var: ${name}`);
  return value;
}

function hmac(key, value, encoding) {
  return crypto.createHmac('sha256', key).update(value).digest(encoding);
}

function sha256(value, encoding = 'hex') {
  return crypto.createHash('sha256').update(value).digest(encoding);
}

function amzDate(date = new Date()) {
  return date.toISOString().replace(/[:-]|\.\d{3}/g, '');
}

function dateStamp(amz) {
  return amz.slice(0, 8);
}

function encodeKey(key) {
  return key.split('/').map(encodeURIComponent).join('/');
}

async function listFiles(dir) {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) files.push(...await listFiles(full));
    else files.push(full);
  }
  return files;
}

function signRequest({ method, url, bodyHash, accessKeyId, secretAccessKey }) {
  const parsed = new URL(url);
  const now = amzDate();
  const day = dateStamp(now);
  const region = 'auto';
  const service = 's3';
  const credentialScope = `${day}/${region}/${service}/aws4_request`;
  const canonicalHeaders = `host:${parsed.host}\nx-amz-content-sha256:${bodyHash}\nx-amz-date:${now}\n`;
  const signedHeaders = 'host;x-amz-content-sha256;x-amz-date';
  const canonicalRequest = [
    method,
    parsed.pathname,
    parsed.searchParams.toString(),
    canonicalHeaders,
    signedHeaders,
    bodyHash,
  ].join('\n');
  const stringToSign = [
    'AWS4-HMAC-SHA256',
    now,
    credentialScope,
    sha256(canonicalRequest),
  ].join('\n');
  const kDate = hmac(`AWS4${secretAccessKey}`, day);
  const kRegion = hmac(kDate, region);
  const kService = hmac(kRegion, service);
  const kSigning = hmac(kService, 'aws4_request');
  const signature = hmac(kSigning, stringToSign, 'hex');
  return {
    authorization: `AWS4-HMAC-SHA256 Credential=${accessKeyId}/${credentialScope}, SignedHeaders=${signedHeaders}, Signature=${signature}`,
    date: now,
  };
}

async function uploadOne({ file, bucket, endpoint, prefix, accessKeyId, secretAccessKey }) {
  const rel = path.relative(SOURCE_DIR, file).replaceAll('\\', '/');
  const key = [prefix, rel].filter(Boolean).join('/').replace(/^\/+/, '');
  const body = await fs.readFile(file);
  const bodyHash = sha256(body);
  const url = `${endpoint}/${bucket}/${encodeKey(key)}`;
  const signature = signRequest({ method: 'PUT', url, bodyHash, accessKeyId, secretAccessKey });
  const response = await fetch(url, {
    method: 'PUT',
    body,
    headers: {
      authorization: signature.authorization,
      'x-amz-content-sha256': bodyHash,
      'x-amz-date': signature.date,
      'content-type': 'image/jpeg',
      'cache-control': 'public, max-age=31536000, immutable',
    },
  });
  if (!response.ok) {
    const text = await response.text().catch(() => '');
    throw new Error(`${response.status} ${response.statusText} uploading ${key}: ${text.slice(0, 300)}`);
  }
  return key;
}

async function runPool(items, concurrency, worker) {
  let next = 0;
  let done = 0;
  const workers = Array.from({ length: concurrency }, async () => {
    while (next < items.length) {
      const item = items[next++];
      await worker(item);
      done += 1;
      if (done % 25 === 0 || done === items.length) console.log(`Uploaded ${done}/${items.length}`);
    }
  });
  await Promise.all(workers);
}

async function main() {
  const accountId = requireEnv('R2_ACCOUNT_ID');
  const accessKeyId = requireEnv('R2_ACCESS_KEY_ID');
  const secretAccessKey = requireEnv('R2_SECRET_ACCESS_KEY');
  const bucket = requireEnv('R2_BUCKET');
  const prefix = (process.env.R2_PREFIX || 'tubs/seedvr-4x').replace(/^\/+|\/+$/g, '');
  const concurrency = Number(process.env.R2_CONCURRENCY || 8);
  const endpoint = `https://${accountId}.r2.cloudflarestorage.com`;

  const files = (await listFiles(SOURCE_DIR)).filter((file) => file.toLowerCase().endsWith('.jpg'));
  if (!files.length) throw new Error(`No jpg files found in ${SOURCE_DIR}`);
  console.log(`Uploading ${files.length} SeedVR images to r2://${bucket}/${prefix}/`);
  await runPool(files, concurrency, (file) => uploadOne({ file, bucket, endpoint, prefix, accessKeyId, secretAccessKey }));

  if (process.env.R2_PUBLIC_BASE_URL) {
    const base = process.env.R2_PUBLIC_BASE_URL.replace(/\/+$/g, '');
    const indexPath = path.join(ROOT, 'public', 'seedvr-4x.json');
    const index = JSON.parse(await fs.readFile(indexPath, 'utf8'));
    index.images = index.images.map((item) => ({
      ...item,
      upscaled: `${base}/${prefix}/${path.basename(item.upscaled)}`,
    }));
    index.remoteBaseUrl = base;
    index.remotePrefix = prefix;
    const out = path.join(ROOT, 'public', 'seedvr-4x.r2.json');
    await fs.writeFile(out, `${JSON.stringify(index, null, 2)}\n`);
    console.log(`Wrote ${path.relative(ROOT, out)}`);
  }
}

main().catch((error) => {
  console.error(error.message || error);
  process.exit(1);
});

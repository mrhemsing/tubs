import fs from 'node:fs';
import path from 'node:path';
import '../styles.css';

function loadSeedvrTest() {
  const file = path.join(process.cwd(), 'public', 'seedvr-test.json');
  if (!fs.existsSync(file)) return { images: [] };
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

export const metadata = {
  title: 'SeedVR 4x Upscale Test',
};

export default function SeedvrTestPage() {
  const data = loadSeedvrTest();
  return (
    <main className="page seedvrPage">
      <section className="hero">
        <div>
          <p className="kicker">Upscale test</p>
          <h1>SeedVR 4x comparison</h1>
          <p className="subtitle">Tiny QA batch only — not wired into the main review flow.</p>
        </div>
        <div className="stats">
          <div className="stat"><div className="statValue">{data.count || data.images.length}</div><div className="statLabel">test images</div></div>
          <div className="stat"><div className="statValue">4.0x</div><div className="statLabel">scale</div></div>
          <div className="stat"><div className="statValue">SeedVR</div><div className="statLabel">model</div></div>
        </div>
      </section>

      <section className="cards seedvrGrid">
        {data.images.map((item) => (
          <article className="card" key={`${item.kind}-${item.listingId}-${item.url}`}>
            <header className="cardHeader">
              <div className="titleBlock">
                <h2>{item.address}</h2>
                <p className="meta">{item.kind} · {item.width || '?'} × {item.height || '?'} · {item.upscale_factor || data.upscale_factor}x</p>
              </div>
              <span className="badge google-overhead-house-backyard-candidate">SeedVR test</span>
            </header>
            <div className="compareGrid">
              <a className="primaryPhoto" href={item.url}>
                <span className="photoLabel">Original</span>
                <img src={item.url} alt={`${item.address} original`} loading="lazy" />
              </a>
              <a className="primaryPhoto" href={item.upscaled}>
                <span className="photoLabel">SeedVR 4x</span>
                <img src={item.upscaled} alt={`${item.address} SeedVR 4x`} loading="lazy" />
              </a>
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}

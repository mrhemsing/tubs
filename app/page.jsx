import fs from 'node:fs';
import path from 'node:path';
import './styles.css';

const labels = {
  mls_drone_or_aerial_candidate: 'MLS aerial/elevated',
  arcgis_overhead_house_backyard_candidate: 'ArcGIS overhead',
  possible_mls_elevated_candidate_needs_verify: 'Possible elevated',
};

function loadData() {
  const file = path.join(process.cwd(), 'public', 'review-data.json');
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

function sourceClass(source) {
  return String(source || '').replaceAll('_', '-');
}

function Stat({ label, value }) {
  return (
    <div className="stat">
      <div className="statValue">{value}</div>
      <div className="statLabel">{label}</div>
    </div>
  );
}

function CandidateCard({ card }) {
  const links = [
    ['MLS contact sheet', card.links?.mlsContactSheet],
    ['ArcGIS contact sheet', card.links?.arcgisContactSheet],
    ['Best ArcGIS tile', card.links?.bestArcgisTile],
  ].filter(([, url]) => url);

  return (
    <article className={`card ${sourceClass(card.recommendedSource)}`}>
      <header className="cardHeader">
        <div className="rank">#{card.rank}</div>
        <div className="titleBlock">
          <h2>{card.address}</h2>
          <p className="meta">List ID {card.listingId} · {card.sourceLabel} · score {card.score}</p>
        </div>
        <span className={`badge ${sourceClass(card.recommendedSource)}`}>
          {labels[card.recommendedSource] || card.recommendedSource}
        </span>
      </header>

      <div className="details">
        <div><b>Best photo indices</b><span>{card.bestPhotoIndices || '—'}</span></div>
        <div><b>Coverage</b><span>{card.coverageGoal || '—'}</span></div>
        <div><b>Coordinate confidence</b><span>{card.coordinateConfidence || '—'}</span></div>
        <div><b>ArcGIS real / placeholder</b><span>{card.arcgisRealTiles || '0'} / {card.arcgisPlaceholderTiles || '0'}</span></div>
      </div>

      <p className="notes">{card.notes}</p>

      {links.length > 0 && (
        <nav className="links">
          {links.map(([label, url]) => <a key={label} href={url}>{label}</a>)}
        </nav>
      )}

      {card.thumbs?.length > 0 && (
        <div className="thumbGrid">
          {card.thumbs.map((thumb, i) => (
            <a className="thumb" href={thumb.url} key={`${thumb.label}-${i}`}>
              <span>{thumb.label}</span>
              <img src={thumb.url} alt={`${card.address} ${thumb.label}`} loading="lazy" />
            </a>
          ))}
        </div>
      )}
    </article>
  );
}

export default function Home() {
  const data = loadData();
  const counts = data.summary.counts;

  return (
    <main>
      <section className="hero">
        <div>
          <p className="eyebrow">Tubs Review</p>
          <h1>Aerial + elevated property candidates</h1>
          <p className="lede">{data.goal}</p>
          <p className="rights">{data.rightsNotice}</p>
        </div>
        <div className="stats">
          <Stat label="Properties" value={data.summary.properties} />
          <Stat label="MLS reviewed" value={data.summary.mlsReviewed} />
          <Stat label="Candidate cards" value={data.summary.candidateCards} />
          <Stat label="MLS aerial/elevated" value={counts.mls_drone_or_aerial_candidate || 0} />
          <Stat label="ArcGIS overhead" value={counts.arcgis_overhead_house_backyard_candidate || 0} />
          <Stat label="Possible elevated" value={counts.possible_mls_elevated_candidate_needs_verify || 0} />
          <Stat label="Needs review" value={counts.needs_aerial_review || 0} />
          <Stat label="No ArcGIS imagery" value={counts.blocked_arcgis_no_imagery || 0} />
        </div>
      </section>

      <section className="toolbar">
        <p>Ranked by strongest available house + backyard/lot aerial or elevated coverage. Open each thumbnail for the full local image exported with this deploy.</p>
      </section>

      <section className="cards">
        {data.cards.map((card) => <CandidateCard card={card} key={`${card.rank}-${card.listingId}`} />)}
      </section>
    </main>
  );
}

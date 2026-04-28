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

function statusLabel(source) {
  return labels[source] || {
    needs_aerial_review: 'Needs aerial review',
    blocked_arcgis_no_imagery: 'No ArcGIS imagery',
    mls_ground_backyard_context_only: 'Ground context only',
    blocked_no_coordinate: 'No coordinate',
  }[source] || source;
}

function Stat({ label, value }) {
  return (
    <div className="stat">
      <div className="statValue">{value}</div>
      <div className="statLabel">{label}</div>
    </div>
  );
}

const areaOrder = ['Columbia Valley', 'Cranbrook/Kimberley', 'Fernie/Sparwood'];
const areaSlugs = {
  'Columbia Valley': 'columbia-valley',
  'Cranbrook/Kimberley': 'cranbrook-kimberley',
  'Fernie/Sparwood': 'fernie-sparwood',
};

function CandidateCard({ card }) {
  const links = [
    ['MLS contact sheet', card.links?.mlsContactSheet],
    ['ArcGIS contact sheet', card.links?.arcgisContactSheet],
    ['Best ArcGIS tile', card.links?.bestArcgisTile],
  ].filter(([, url]) => url);
  const primary = card.thumbs?.[0];
  const remaining = card.thumbs?.slice(1) || [];

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

      <div className="listingLayout">
        <section className="photoPanel">
          {primary ? (
            <a className="primaryPhoto" href={primary.url}>
              <span className="photoLabel">Best candidate {primary.label}</span>
              <img src={primary.url} alt={`${card.address} best candidate ${primary.label}`} loading="lazy" />
            </a>
          ) : (
            <div className="primaryPhoto empty">No exported candidate photo</div>
          )}
          {remaining.length > 0 && (
            <div className="thumbGrid compact">
              {remaining.map((thumb, i) => (
                <a className="thumb" href={thumb.url} key={`${thumb.label}-${i}`}>
                  <span>{thumb.label}</span>
                  <img src={thumb.url} alt={`${card.address} ${thumb.label}`} loading="lazy" />
                </a>
              ))}
            </div>
          )}
        </section>

        <section className="infoPanel">
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
        </section>
      </div>
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
        <p>Ranked by strongest available house + backyard/lot aerial or elevated coverage. Each listing shows the actual best candidate photo first, followed by remaining candidate photos.</p>
        <nav className="areaNav" aria-label="Area navigation">
          {areaOrder.map((area) => (
            <a href={`#${areaSlugs[area]}`} key={area}>{area}</a>
          ))}
          <a href="#all-addresses">All addresses</a>
        </nav>
      </section>

      {areaOrder.map((area) => {
        const cards = data.cards.filter((card) => card.sourceLabel === area);
        if (cards.length === 0) return null;
        const aerialCount = cards.filter((card) => card.recommendedSource === 'mls_drone_or_aerial_candidate').length;
        const arcgisCount = cards.filter((card) => card.recommendedSource === 'arcgis_overhead_house_backyard_candidate').length;
        const possibleCount = cards.filter((card) => card.recommendedSource === 'possible_mls_elevated_candidate_needs_verify').length;
        return (
          <section className="areaSection" key={area} id={areaSlugs[area]}>
            <div className="areaHeader">
              <div>
                <p className="areaKicker">Area</p>
                <h2>{area}</h2>
              </div>
              <div className="areaStats">
                <span>{cards.length} candidates</span>
                <span>{aerialCount} MLS aerial/elevated</span>
                <span>{arcgisCount} ArcGIS overhead</span>
                <span>{possibleCount} possible elevated</span>
              </div>
            </div>
            <div className="cards">
              {cards.map((card) => <CandidateCard card={card} key={`${card.rank}-${card.listingId}`} />)}
            </div>
          </section>
        );
      })}

      <div id="all-addresses" className="anchorLabel">All addresses</div>
      {areaOrder.map((area) => {
        const rows = data.allAddresses.filter((row) => row.sourceLabel === area);
        return (
          <section className="addressSection" key={`${area}-all`}>
            <div className="areaHeader compactHeader">
              <div>
                <p className="areaKicker">All addresses</p>
                <h2>{area}</h2>
              </div>
              <div className="areaStats"><span>{rows.length} total properties</span></div>
            </div>
            <div className="tableWrap">
              <table>
                <thead>
                  <tr>
                    <th>Address</th>
                    <th>Status</th>
                    <th>Best photos</th>
                    <th>MLS reviewed</th>
                    <th>ArcGIS tiles</th>
                    <th>Coordinate</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => (
                    <tr key={row.listingId} className={sourceClass(row.recommendedSource)}>
                      <td><b>{row.address}</b><span>{row.listingId}</span></td>
                      <td>{statusLabel(row.recommendedSource)}</td>
                      <td>{row.bestPhotoIndices || '—'}</td>
                      <td>{row.mlsReviewed ? row.mlsAerial : 'No'}</td>
                      <td>{row.arcgisRealTiles || '0'} / {row.arcgisPlaceholderTiles || '0'}</td>
                      <td>{row.coordinateConfidence}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        );
      })}
    </main>
  );
}

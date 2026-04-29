import fs from 'node:fs';
import path from 'node:path';

const labels = {
  mls_drone_or_aerial_candidate: 'MLS aerial/elevated',
  arcgis_overhead_house_backyard_candidate: 'ArcGIS overhead',
  bing_overhead_house_backyard_candidate: 'Bing overhead',
  mapbox_overhead_house_backyard_candidate: 'Mapbox overhead',
  possible_mls_elevated_candidate_needs_verify: 'Possible elevated',
  possible_bing_overhead_needs_verify: 'Possible Bing overhead',
  possible_mapbox_overhead_needs_verify: 'Possible Mapbox overhead',
};

export const areaOrder = ['Columbia Valley', 'Cranbrook/Kimberley', 'Fernie/Sparwood'];
export const areaSlugs = {
  'Columbia Valley': 'columbia-valley',
  'Cranbrook/Kimberley': 'cranbrook-kimberley',
  'Fernie/Sparwood': 'fernie-sparwood',
};
const mobileAreaLabels = {
  'Columbia Valley': ['Columbia', 'Valley'],
  'Cranbrook/Kimberley': ['Cranbrook', 'Kimberley'],
  'Fernie/Sparwood': ['Fernie', 'Sparwood'],
};
export const slugToArea = Object.fromEntries(Object.entries(areaSlugs).map(([area, slug]) => [slug, area]));
const areaBanners = {
  'Columbia Valley': '/banner-columbia-valley.jpg',
  'Cranbrook/Kimberley': '/banner-cranbrook-kimberley.jpg',
  'Fernie/Sparwood': '/banner-fernie-sparwood.jpg',
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
    blocked_arcgis_no_imagery: 'ArcGIS overhead unavailable',
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

function CandidateCard({ card, displayRank = card.rank }) {
  const links = [
    ['MLS contact sheet', card.links?.mlsContactSheet],
    ['ArcGIS contact sheet', card.links?.arcgisContactSheet],
    ['Best ArcGIS tile', card.links?.bestArcgisTile],
    ['Bing contact sheet', card.links?.bingContactSheet],
    ['Mapbox contact sheet', card.links?.mapboxContactSheet],
  ].filter(([, url]) => url);
  const primary = card.thumbs?.[0];
  const remaining = card.thumbs?.slice(1) || [];

  return (
    <article className={`card ${sourceClass(card.recommendedSource)}`}>
      <header className="cardHeader">
        <div className="rank">#{displayRank}</div>
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
            <div><b>Bing overhead</b><span>{card.bingOverhead && card.bingOverhead !== 'unreviewed' ? `${card.bingOverhead} · ${card.bingCoverageStrength || '—'}` : '—'}</span></div>
            <div><b>Bing best tile</b><span>{card.bingBestTilePosition || '—'}</span></div>
            <div><b>Mapbox overhead</b><span>{card.mapboxOverhead && card.mapboxOverhead !== 'unreviewed' ? `${card.mapboxOverhead} · ${card.mapboxCoverageStrength || '—'}` : '—'}</span></div>
            <div><b>Mapbox best tile</b><span>{card.mapboxBestTilePosition || '—'}</span></div>
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

function AreaBlock({ area, cards, rows }) {
  const aerialCount = cards.filter((card) => card.recommendedSource === 'mls_drone_or_aerial_candidate').length;
  const arcgisCount = cards.filter((card) => card.recommendedSource === 'arcgis_overhead_house_backyard_candidate').length;
  const bingCount = cards.filter((card) => card.recommendedSource === 'bing_overhead_house_backyard_candidate').length;
  const mapboxCount = cards.filter((card) => card.recommendedSource === 'mapbox_overhead_house_backyard_candidate').length;
  const possibleCount = cards.filter((card) => ['possible_mls_elevated_candidate_needs_verify', 'possible_bing_overhead_needs_verify', 'possible_mapbox_overhead_needs_verify'].includes(card.recommendedSource)).length;

  return (
    <section className="areaSection" id={areaSlugs[area]}>
      <div className="areaBanner">
        <img src={areaBanners[area]} alt={`${area} banner illustration`} loading="lazy" />
        <div className="areaBannerOverlay">
          <div className="areaBannerTitle">
            <p className="areaKicker">Area</p>
            <h2>{area}</h2>
          </div>
          <div className="areaStats">
            <span>{cards.length}/{rows.length} candidates</span>
            <span>{aerialCount} MLS aerial/elevated</span>
            <span>{arcgisCount} ArcGIS overhead</span>
            <span>{bingCount} Bing overhead</span>
            <span>{mapboxCount} Mapbox overhead</span>
            <span>{possibleCount} possible elevated</span>
          </div>
        </div>
      </div>

      <div className="cards">
        {cards.map((card, index) => <CandidateCard card={card} displayRank={index + 1} key={`${card.rank}-${card.listingId}`} />)}
      </div>

      <section className="addressSection">
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
                <th>Bing</th>
                <th>Mapbox</th>
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
                  <td>{row.bingOverhead && row.bingOverhead !== 'unreviewed' ? row.bingOverhead : '—'}</td>
                  <td>{row.mapboxOverhead && row.mapboxOverhead !== 'unreviewed' ? row.mapboxOverhead : '—'}</td>
                  <td>{row.coordinateConfidence}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </section>
  );
}

export default function ReviewPage({ areaFilter = null }) {
  const data = loadData();
  const counts = data.summary.counts;
  const pageAreas = areaFilter ? [areaFilter] : areaOrder;
  const title = areaFilter === 'Cranbrook/Kimberley'
    ? 'Cranbrook & Kimberley aerial candidates'
    : areaFilter === 'Fernie/Sparwood'
      ? 'Fernie & Sparwood aerial candidates'
      : areaFilter
        ? `${areaFilter} aerial candidates`
        : 'Aerial + elevated property candidates';

  return (
    <main>
      <section className="toolbar">
        <nav className="areaNav" aria-label="Area navigation">
          {areaOrder.map((area) => (
            <a className={area === areaFilter || (!areaFilter && area === 'Columbia Valley') ? 'active' : ''} href={`/${areaSlugs[area]}`} key={area}>
              <span className="navDesktopLabel">{area}</span>
              <span className="navMobileLabel">{mobileAreaLabels[area].map((part) => <span key={part}>{part}</span>)}</span>
            </a>
          ))}
        </nav>
      </section>

      {pageAreas.map((area) => {
        const cards = data.cards.filter((card) => card.sourceLabel === area);
        const rows = data.allAddresses.filter((row) => row.sourceLabel === area);
        return <AreaBlock area={area} cards={cards} rows={rows} key={area} />;
      })}
    </main>
  );
}

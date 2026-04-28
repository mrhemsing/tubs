import fs from 'node:fs';
import path from 'node:path';

const labels = {
  mls_drone_or_aerial_candidate: 'MLS aerial/elevated',
  arcgis_overhead_house_backyard_candidate: 'ArcGIS overhead',
  possible_mls_elevated_candidate_needs_verify: 'Possible elevated',
};

export const areaOrder = ['Columbia Valley', 'Cranbrook/Kimberley', 'Fernie/Sparwood'];
export const areaSlugs = {
  'Columbia Valley': 'columbia-valley',
  'Cranbrook/Kimberley': 'cranbrook-kimberley',
  'Fernie/Sparwood': 'fernie-sparwood',
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

function CandidateCard({ card, displayRank = card.rank }) {
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
  const possibleCount = cards.filter((card) => card.recommendedSource === 'possible_mls_elevated_candidate_needs_verify').length;

  return (
    <section className="areaSection" id={areaSlugs[area]}>
      <div className="areaBanner">
        <img src={areaBanners[area]} alt={`${area} banner illustration`} loading="lazy" />
        <div className="areaBannerOverlay">
          <p className="areaKicker">Area</p>
          <h2>{area}</h2>
          <div className="areaStats">
            <span>{cards.length} candidates</span>
            <span>{aerialCount} MLS aerial/elevated</span>
            <span>{arcgisCount} ArcGIS overhead</span>
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
    </section>
  );
}

export default function ReviewPage({ areaFilter = null }) {
  const data = loadData();
  const counts = data.summary.counts;
  const pageAreas = areaFilter ? [areaFilter] : areaOrder;
  const title = areaFilter === 'Cranbrook/Kimberley'
    ? 'Cranbrook & Kimberley aerial candidates'
    : areaFilter
      ? `${areaFilter} aerial candidates`
      : 'Aerial + elevated property candidates';

  return (
    <main>
      <section className="hero">
        <div className="heroCopy">
          <p className="eyebrow">Tubs Review</p>
          <h1>{title}</h1>
          <p className="lede">{data.goal}</p>
          <p className="rights">{data.rightsNotice}</p>
        </div>
        <div className="heroArtWrap">
          <img className="heroArt" src="/header-illustration.jpg" alt="Illustration of friends in a snowy mountain hot tub" />
        </div>
        <div className="stats">
          <Stat label="Properties" value={areaFilter ? data.allAddresses.filter((row) => row.sourceLabel === areaFilter).length : data.summary.properties} />
          <Stat label="MLS reviewed" value={areaFilter ? data.allAddresses.filter((row) => row.sourceLabel === areaFilter && row.mlsReviewed).length : data.summary.mlsReviewed} />
          <Stat label="Candidate cards" value={areaFilter ? data.cards.filter((card) => card.sourceLabel === areaFilter).length : data.summary.candidateCards} />
          <Stat label="MLS aerial/elevated" value={areaFilter ? data.cards.filter((card) => card.sourceLabel === areaFilter && card.recommendedSource === 'mls_drone_or_aerial_candidate').length : counts.mls_drone_or_aerial_candidate || 0} />
          <Stat label="ArcGIS overhead" value={areaFilter ? data.cards.filter((card) => card.sourceLabel === areaFilter && card.recommendedSource === 'arcgis_overhead_house_backyard_candidate').length : counts.arcgis_overhead_house_backyard_candidate || 0} />
          <Stat label="Possible elevated" value={areaFilter ? data.cards.filter((card) => card.sourceLabel === areaFilter && card.recommendedSource === 'possible_mls_elevated_candidate_needs_verify').length : counts.possible_mls_elevated_candidate_needs_verify || 0} />
          <Stat label="Needs review" value={areaFilter ? data.allAddresses.filter((row) => row.sourceLabel === areaFilter && row.recommendedSource === 'needs_aerial_review').length : counts.needs_aerial_review || 0} />
          <Stat label="No ArcGIS imagery" value={areaFilter ? data.allAddresses.filter((row) => row.sourceLabel === areaFilter && row.recommendedSource === 'blocked_arcgis_no_imagery').length : counts.blocked_arcgis_no_imagery || 0} />
        </div>
      </section>

      <section className="toolbar">
        <p>{areaFilter ? `Showing only ${areaFilter}.` : 'Choose a dedicated area page, or view all areas below.'}</p>
        <nav className="areaNav" aria-label="Area navigation">
          {areaOrder.map((area) => (
            <a className={area === areaFilter || (!areaFilter && area === 'Columbia Valley') ? 'active' : ''} href={`/${areaSlugs[area]}`} key={area}>{area}</a>
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

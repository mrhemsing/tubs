'use client';

import { useEffect, useRef, useState } from 'react';

const fallbackPlacement = { xPct: 58, yPct: 62, sizePct: 18, rotation: 0 };

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function roundedRectPath(ctx, x, y, w, h, r) {
  const radius = Math.min(r, w / 2, h / 2);
  ctx.beginPath();
  ctx.moveTo(x + radius, y);
  ctx.arcTo(x + w, y, x + w, y + h, radius);
  ctx.arcTo(x + w, y + h, x, y + h, radius);
  ctx.arcTo(x, y + h, x, y, radius);
  ctx.arcTo(x, y, x + w, y, radius);
  ctx.closePath();
}

function drawJet(ctx, x, y, r, rotation = 0) {
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(rotation);
  const jet = ctx.createRadialGradient(-r * 0.25, -r * 0.25, r * 0.15, 0, 0, r);
  jet.addColorStop(0, '#f8fafc');
  jet.addColorStop(0.55, '#64748b');
  jet.addColorStop(1, '#111827');
  ctx.fillStyle = jet;
  ctx.beginPath();
  ctx.ellipse(0, 0, r, r * 0.7, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = 'rgba(255,255,255,.7)';
  ctx.beginPath();
  ctx.ellipse(-r * 0.18, -r * 0.13, r * 0.28, r * 0.16, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}

function drawTub(ctx, centerX, centerY, size, rotationDeg) {
  ctx.save();
  ctx.translate(centerX, centerY);
  ctx.rotate((rotationDeg * Math.PI) / 180);
  ctx.translate(-size / 2, -size / 2);

  const radius = size * 0.11;
  ctx.shadowColor = 'rgba(0,0,0,.36)';
  ctx.shadowBlur = size * 0.07;
  ctx.shadowOffsetX = size * 0.035;
  ctx.shadowOffsetY = size * 0.055;

  const shell = ctx.createLinearGradient(0, 0, size, size);
  shell.addColorStop(0, '#ffffff');
  shell.addColorStop(0.5, '#eef2f7');
  shell.addColorStop(1, '#d9e2ec');
  ctx.fillStyle = shell;
  ctx.strokeStyle = 'rgba(15,23,42,.45)';
  ctx.lineWidth = Math.max(2, size * 0.014);
  roundedRectPath(ctx, 0, 0, size, size, radius);
  ctx.fill();
  ctx.stroke();

  ctx.shadowColor = 'transparent';

  // Sculpted shell basins / seating lobes.
  const seatFill = ctx.createLinearGradient(0, 0, size, size);
  seatFill.addColorStop(0, 'rgba(255,255,255,.82)');
  seatFill.addColorStop(1, 'rgba(203,213,225,.52)');
  ctx.fillStyle = seatFill;
  const lobes = [
    [size * 0.23, size * 0.27, size * 0.18, size * 0.25, -0.52],
    [size * 0.74, size * 0.25, size * 0.22, size * 0.17, 0.2],
    [size * 0.78, size * 0.74, size * 0.2, size * 0.2, -0.34],
    [size * 0.26, size * 0.78, size * 0.2, size * 0.18, 0.48],
  ];
  for (const [x, y, rx, ry, rot] of lobes) {
    ctx.beginPath();
    ctx.ellipse(x, y, rx, ry, rot, 0, Math.PI * 2);
    ctx.fill();
  }

  // Irregular water area like a real spa interior.
  const water = ctx.createRadialGradient(size * 0.36, size * 0.33, size * 0.03, size * 0.52, size * 0.55, size * 0.48);
  water.addColorStop(0, '#f6feff');
  water.addColorStop(0.28, '#d8f8ff');
  water.addColorStop(0.64, '#9be3f3');
  water.addColorStop(1, '#60c7df');
  ctx.fillStyle = water;
  ctx.strokeStyle = 'rgba(255,255,255,.92)';
  ctx.lineWidth = Math.max(3, size * 0.018);
  ctx.beginPath();
  ctx.moveTo(size * 0.25, size * 0.18);
  ctx.bezierCurveTo(size * 0.42, size * 0.1, size * 0.5, size * 0.27, size * 0.62, size * 0.19);
  ctx.bezierCurveTo(size * 0.83, size * 0.1, size * 0.91, size * 0.28, size * 0.84, size * 0.45);
  ctx.bezierCurveTo(size * 0.98, size * 0.62, size * 0.82, size * 0.91, size * 0.64, size * 0.82);
  ctx.bezierCurveTo(size * 0.48, size * 0.94, size * 0.38, size * 0.78, size * 0.23, size * 0.84);
  ctx.bezierCurveTo(size * 0.05, size * 0.77, size * 0.16, size * 0.58, size * 0.19, size * 0.46);
  ctx.bezierCurveTo(size * 0.07, size * 0.32, size * 0.11, size * 0.21, size * 0.25, size * 0.18);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();

  // Subtle water ripples.
  ctx.strokeStyle = 'rgba(255,255,255,.42)';
  ctx.lineWidth = Math.max(1, size * 0.006);
  for (const [x, y, rx, ry, rot] of [
    [0.42, 0.37, 0.19, 0.07, -0.2], [0.58, 0.56, 0.22, 0.08, 0.18], [0.34, 0.67, 0.15, 0.055, 0.5]
  ]) {
    ctx.beginPath();
    ctx.ellipse(size * x, size * y, size * rx, size * ry, rot, 0.2, Math.PI * 1.55);
    ctx.stroke();
  }

  // Black headrests.
  ctx.fillStyle = '#111827';
  for (const [x, y, w, h, rot] of [
    [0.2, 0.16, 0.18, 0.055, -0.55], [0.82, 0.17, 0.18, 0.055, 0.55],
    [0.83, 0.84, 0.18, 0.055, -0.75], [0.17, 0.84, 0.18, 0.055, 0.75]
  ]) {
    ctx.save();
    ctx.translate(size * x, size * y);
    ctx.rotate(rot);
    roundedRectPath(ctx, -size * w / 2, -size * h / 2, size * w, size * h, size * h / 2);
    ctx.fill();
    ctx.restore();
  }

  // Control panel.
  const panelW = size * 0.17;
  const panelH = size * 0.075;
  ctx.fillStyle = '#334155';
  roundedRectPath(ctx, size * 0.415, size * 0.035, panelW, panelH, size * 0.018);
  ctx.fill();
  ctx.fillStyle = '#94a3b8';
  roundedRectPath(ctx, size * 0.448, size * 0.052, panelW * 0.34, panelH * 0.25, size * 0.006);
  ctx.fill();
  ctx.fillStyle = '#e2e8f0';
  ctx.beginPath(); ctx.arc(size * 0.53, size * 0.064, size * 0.008, 0, Math.PI * 2); ctx.fill();

  // Jets around seats and footwell.
  const jets = [
    [0.28,0.30,.023,-.2],[0.22,0.36,.02,.2],[0.31,0.43,.018,.4],[0.75,0.31,.022,.1],[0.82,0.39,.018,-.2],
    [0.73,0.66,.021,.5],[0.81,0.72,.019,.1],[0.68,0.78,.018,-.2],[0.30,0.73,.02,.1],[0.22,0.66,.018,-.3],
    [0.45,0.54,.018,0],[0.56,0.51,.019,.1],[0.52,0.70,.018,.1],[0.61,0.67,.016,.1]
  ];
  for (const [x, y, r, rot] of jets) drawJet(ctx, size * x, size * y, size * r, rot);

  // Small round drains / cup details on shell.
  ctx.fillStyle = '#1f2937';
  for (const [x, y, r] of [[0.38,0.09,.026],[0.62,0.09,.026],[0.09,0.48,.022],[0.91,0.5,.022],[0.5,0.91,.026]]) {
    ctx.beginPath(); ctx.arc(size * x, size * y, size * r, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#cbd5e1'; ctx.beginPath(); ctx.arc(size * x, size * y, size * r * .45, 0, Math.PI * 2); ctx.fill(); ctx.fillStyle = '#1f2937';
  }

  ctx.restore();
}

export default function TubDesigner({ listingId, address, sourceImage, imageOptions = [], initialPlacement }) {
  const normalizedOptions = [
    ...imageOptions.filter((option) => option?.url),
    sourceImage ? { label: 'Tub design base', url: sourceImage } : null,
  ].filter(Boolean).filter((option, index, all) => all.findIndex((item) => item.url === option.url) === index);
  const storageKey = `tub-placement:${listingId}`;
  const imageStorageKey = `tub-design-image:${listingId}`;
  const savedMockupKey = `tub-saved-mockup:${listingId}`;
  const boxRef = useRef(null);
  const stageRef = useRef(null);
  const imageRef = useRef(null);
  const dragging = useRef(false);
  const [open, setOpen] = useState(false);
  const [placement, setPlacement] = useState({ ...fallbackPlacement, ...(initialPlacement || {}) });
  const [selectedImage, setSelectedImage] = useState(sourceImage || normalizedOptions[0]?.url || '');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [saveMessage, setSaveMessage] = useState('');

  useEffect(() => {
    try {
      const saved = window.localStorage.getItem(storageKey);
      if (saved) setPlacement((current) => ({ ...current, ...JSON.parse(saved) }));
      const savedImage = window.localStorage.getItem(imageStorageKey);
      if (savedImage && normalizedOptions.some((option) => option.url === savedImage)) setSelectedImage(savedImage);
      const savedMockup = window.localStorage.getItem(savedMockupKey);
      if (savedMockup) window.setTimeout(() => applySavedMockup(JSON.parse(savedMockup)), 0);
    } catch {}
  }, [storageKey, imageStorageKey, savedMockupKey]);

  useEffect(() => {
    try {
      window.localStorage.setItem(storageKey, JSON.stringify(placement));
    } catch {}
  }, [storageKey, placement]);

  useEffect(() => {
    try {
      if (selectedImage) window.localStorage.setItem(imageStorageKey, selectedImage);
    } catch {}
  }, [imageStorageKey, selectedImage]);

  if (!selectedImage) return null;

  function setPoint(clientX, clientY) {
    const rect = stageRef.current?.getBoundingClientRect();
    if (!rect) return;
    setPlacement((current) => ({
      ...current,
      xPct: Number(clamp(((clientX - rect.left) / rect.width) * 100, 2, 98).toFixed(2)),
      yPct: Number(clamp(((clientY - rect.top) / rect.height) * 100, 2, 98).toFixed(2)),
    }));
  }

  function buildSavedTubNode(savedPlacement) {
    const tub = document.createElement('div');
    tub.className = 'designTub savedConceptTub';
    tub.style.left = `${savedPlacement.xPct}%`;
    tub.style.top = `${savedPlacement.yPct}%`;
    tub.style.width = `${savedPlacement.sizePct}%`;
    tub.style.transform = `translate(-50%, -50%) rotate(${savedPlacement.rotation}deg)`;

    const water = document.createElement('div');
    water.className = 'designTubWater';
    tub.appendChild(water);

    const panel = document.createElement('div');
    panel.className = 'designTubPanel';
    tub.appendChild(panel);

    for (let i = 1; i <= 18; i += 1) {
      const jet = document.createElement('span');
      jet.className = `designTubJet jet${i}`;
      tub.appendChild(jet);
    }

    return tub;
  }

  function applySavedMockup(savedMockup) {
    const article = boxRef.current?.closest('article');
    const link = article?.querySelector('.tubMockup');
    const img = link?.querySelector('img');
    const label = link?.querySelector('.photoLabel');
    const note = link?.querySelector('em');
    const savedPlacement = savedMockup?.placement || placement;
    const savedSourceImage = savedMockup?.sourceImage || selectedImage;
    if (!link || !img || !savedSourceImage) return false;

    img.src = savedSourceImage;
    link.href = savedSourceImage;
    link.classList.add('savedConceptMockup');
    if (label) label.textContent = 'Tub concept mockup - saved edit';
    if (note) note.textContent = 'Saved concept mockup - hot tub digitally added.';
    link.querySelectorAll('.savedConceptTub').forEach((node) => node.remove());
    const tub = buildSavedTubNode(savedPlacement);
    if (tub) link.insertBefore(tub, note || null);
    return true;
  }

  function saveEditedMockup() {
    setSaving(true);
    try {
      const savedMockup = { sourceImage: selectedImage, placement };
      window.localStorage.setItem(savedMockupKey, JSON.stringify(savedMockup));
      const applied = applySavedMockup(savedMockup);
      setSaved(true);
      setSaveMessage(applied ? 'Saved - Tub concept mockup updated above.' : 'Saved - refresh if the concept mockup does not update.');
      setTimeout(() => {
        setSaved(false);
        setSaveMessage('');
      }, 2600);
    } catch (error) {
      setSaveMessage('Could not save in this browser. Try clearing site storage and saving again.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="designerBox" ref={boxRef}>
      <button className="designerToggle" type="button" onClick={() => setOpen((value) => !value)}>
        {open ? 'Hide editable tub layer' : 'Edit tub layer'}
      </button>
      {open && (
        <div className="designerPanel">
          <div className="designerStatus">Design base: selected photo - tub overlay: sharp vector export</div>
          {normalizedOptions.length > 1 && (
            <label className="designerPhotoPicker">
              Photo to edit
              <select value={selectedImage} onChange={(event) => setSelectedImage(event.target.value)}>
                {normalizedOptions.map((option) => (
                  <option value={option.url} key={option.url}>{option.label}</option>
                ))}
              </select>
            </label>
          )}
          <div
            ref={stageRef}
            className="designerStage"
            onPointerDown={(event) => {
              dragging.current = true;
              event.currentTarget.setPointerCapture(event.pointerId);
              setPoint(event.clientX, event.clientY);
            }}
            onPointerMove={(event) => {
              if (dragging.current) setPoint(event.clientX, event.clientY);
            }}
            onPointerUp={() => { dragging.current = false; }}
            onPointerCancel={() => { dragging.current = false; }}
          >
            <img ref={imageRef} src={selectedImage} alt={`${address} tub design base`} loading="lazy" draggable="false" />
            <div
              className="designTub"
              style={{
                left: `${placement.xPct}%`,
                top: `${placement.yPct}%`,
                width: `${placement.sizePct}%`,
                transform: `translate(-50%, -50%) rotate(${placement.rotation}deg)`,
              }}
              aria-label="Editable hot tub overlay"
            >
              <div className="designTubWater" />
              <div className="designTubPanel" />
              {Array.from({ length: 18 }, (_, index) => <span className={`designTubJet jet${index + 1}`} key={index} />)}
            </div>
          </div>
          <div className="designerControls">
            <label>
              Size
              <input
                type="range"
                min="8"
                max="34"
                step="0.5"
                value={placement.sizePct}
                onChange={(event) => setPlacement((current) => ({ ...current, sizePct: Number(event.target.value) }))}
              />
            </label>
            <label>
              Rotate
              <input
                type="range"
                min="-45"
                max="45"
                step="1"
                value={placement.rotation}
                onChange={(event) => setPlacement((current) => ({ ...current, rotation: Number(event.target.value) }))}
              />
            </label>
            <div className="designerButtons">
              <button type="button" onClick={() => setPlacement({ ...fallbackPlacement, ...(initialPlacement || {}) })}>Reset</button>
              <button type="button" onClick={saveEditedMockup} disabled={saving}>{saving ? 'Saving...' : saved ? 'Saved ✓' : 'Save'}</button>
            </div>
          </div>
          {saveMessage && <p className="designerSaveNotice">{saveMessage}</p>}
          <p className="designerHint">Drag the tub on the real source image, resize/rotate it, then Save to replace the Tub concept mockup for this address in this browser.</p>
        </div>
      )}
    </section>
  );
}

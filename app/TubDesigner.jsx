'use client';

import { useEffect, useRef, useState } from 'react';

const fallbackPlacement = { xPct: 58, yPct: 62, sizePct: 18, rotation: 0 };

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function drawTub(ctx, centerX, centerY, size, rotationDeg) {
  ctx.save();
  ctx.translate(centerX, centerY);
  ctx.rotate((rotationDeg * Math.PI) / 180);
  ctx.translate(-size / 2, -size / 2);

  const radius = size * 0.22;
  ctx.shadowColor = 'rgba(0,0,0,.34)';
  ctx.shadowBlur = size * 0.06;
  ctx.shadowOffsetX = size * 0.035;
  ctx.shadowOffsetY = size * 0.055;
  ctx.fillStyle = '#f8fafc';
  ctx.strokeStyle = 'rgba(15,23,42,.38)';
  ctx.lineWidth = Math.max(3, size * 0.018);
  ctx.beginPath();
  ctx.roundRect(0, 0, size, size, radius);
  ctx.fill();
  ctx.stroke();

  ctx.shadowColor = 'transparent';
  const inset = size * 0.18;
  const water = ctx.createRadialGradient(size * 0.38, size * 0.36, size * 0.03, size * 0.5, size * 0.55, size * 0.42);
  water.addColorStop(0, '#efffff');
  water.addColorStop(0.48, '#7dd3fc');
  water.addColorStop(1, '#38bdf8');
  ctx.fillStyle = water;
  ctx.strokeStyle = 'rgba(255,255,255,.88)';
  ctx.lineWidth = Math.max(3, size * 0.02);
  ctx.beginPath();
  ctx.roundRect(inset, inset, size - inset * 2, size - inset * 2, size * 0.19);
  ctx.fill();
  ctx.stroke();

  ctx.fillStyle = 'rgba(15,23,42,.72)';
  ctx.beginPath();
  ctx.ellipse(size * 0.26, size * 0.21, size * 0.1, size * 0.05, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.beginPath();
  ctx.ellipse(size * 0.74, size * 0.79, size * 0.1, size * 0.05, 0, 0, Math.PI * 2);
  ctx.fill();

  ctx.restore();
}

export default function TubDesigner({ listingId, address, sourceImage, initialPlacement }) {
  const storageKey = `tub-placement:${listingId}`;
  const stageRef = useRef(null);
  const imageRef = useRef(null);
  const dragging = useRef(false);
  const [open, setOpen] = useState(false);
  const [placement, setPlacement] = useState({ ...fallbackPlacement, ...(initialPlacement || {}) });
  const [copied, setCopied] = useState(false);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    try {
      const saved = window.localStorage.getItem(storageKey);
      if (saved) setPlacement((current) => ({ ...current, ...JSON.parse(saved) }));
    } catch {}
  }, [storageKey]);

  useEffect(() => {
    try {
      window.localStorage.setItem(storageKey, JSON.stringify(placement));
    } catch {}
  }, [storageKey, placement]);

  if (!sourceImage) return null;

  function setPoint(clientX, clientY) {
    const rect = stageRef.current?.getBoundingClientRect();
    if (!rect) return;
    setPlacement((current) => ({
      ...current,
      xPct: Number(clamp(((clientX - rect.left) / rect.width) * 100, 2, 98).toFixed(2)),
      yPct: Number(clamp(((clientY - rect.top) / rect.height) * 100, 2, 98).toFixed(2)),
    }));
  }

  function copyJson() {
    const payload = JSON.stringify({ listingId, address, sourceImage, placement }, null, 2);
    navigator.clipboard?.writeText(payload);
    setCopied(true);
    setTimeout(() => setCopied(false), 1200);
  }

  async function exportEditedMockup() {
    const img = imageRef.current;
    if (!img?.complete || !img.naturalWidth) return;
    setExporting(true);
    try {
      const canvas = document.createElement('canvas');
      canvas.width = img.naturalWidth;
      canvas.height = img.naturalHeight;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      const size = (placement.sizePct / 100) * canvas.width;
      drawTub(ctx, (placement.xPct / 100) * canvas.width, (placement.yPct / 100) * canvas.height, size, placement.rotation);
      const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg', 0.92));
      if (!blob) return;
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${address.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || listingId}-edited-tub-4x.jpg`;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setExporting(false);
    }
  }

  return (
    <section className="designerBox">
      <button className="designerToggle" type="button" onClick={() => setOpen((value) => !value)}>
        {open ? 'Hide editable tub layer' : 'Edit tub layer'}
      </button>
      {open && (
        <div className="designerPanel">
          <div className="designerStatus">Design base: original · tub overlay: sharp vector export</div>
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
            <img ref={imageRef} src={sourceImage} alt={`${address} tub design base`} loading="lazy" draggable="false" />
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
              <button type="button" onClick={copyJson}>{copied ? 'Copied' : 'Copy placement JSON'}</button>
              <button type="button" onClick={exportEditedMockup} disabled={exporting}>{exporting ? 'Exporting…' : 'Download edited mockup'}</button>
            </div>
          </div>
          <p className="designerHint">Drag the tub on the real source image, resize/rotate it, then download an edited mockup or copy placement JSON for permanent tuning.</p>
        </div>
      )}
    </section>
  );
}

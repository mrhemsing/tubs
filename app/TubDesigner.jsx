'use client';

import { useEffect, useRef, useState } from 'react';

const fallbackPlacement = { xPct: 58, yPct: 62, sizePct: 18, rotation: 0 };

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

export default function TubDesigner({ listingId, address, sourceImage, initialPlacement }) {
  const storageKey = `tub-placement:${listingId}`;
  const stageRef = useRef(null);
  const dragging = useRef(false);
  const [open, setOpen] = useState(false);
  const [placement, setPlacement] = useState({ ...fallbackPlacement, ...(initialPlacement || {}) });
  const [copied, setCopied] = useState(false);

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
    const payload = JSON.stringify({ listingId, address, placement }, null, 2);
    navigator.clipboard?.writeText(payload);
    setCopied(true);
    setTimeout(() => setCopied(false), 1200);
  }

  return (
    <section className="designerBox">
      <button className="designerToggle" type="button" onClick={() => setOpen((value) => !value)}>
        {open ? 'Hide tub design layer' : 'Adjust tub design layer'}
      </button>
      {open && (
        <div className="designerPanel">
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
            <img src={sourceImage} alt={`${address} tub design base`} loading="lazy" draggable="false" />
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
            </div>
          </div>
          <p className="designerHint">Drag the tub on the image, resize/rotate it, then copy the placement JSON for permanent tuning.</p>
        </div>
      )}
    </section>
  );
}

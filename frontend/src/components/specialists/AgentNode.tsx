/**
 * AgentNode — reference implementation of the animated agent circle.
 *
 * The SVG avatar MUST be inline (not <img>, not next/image, not CSS background):
 * the animations move parts inside the SVG (eyes, mouth, head group, status light).
 * Internals animate with plain CSS (agent-node.css). framer-motion handles only
 * the outer wrapper (enter/exit, layout) and the agreement badge, on separate elements,
 * so it never overwrites the CSS transforms.
 */
import React, { memo, useEffect, useMemo, useRef, useState } from 'react';
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion';
import '../../styles/agent-node.css';

export type AgentState = 'idle' | 'thinking' | 'speaking' | 'listening' | 'agreed' | 'standby';

export interface AgentNodeProps {
  agentKey: string;          // 'ob', 'em', ...
  name: string;              // 'Obstetrics'
  color: string;             // '#2E9FE6'
  svg: string;               // raw markup of vh-agent-<specialty>-compact.svg
  state: AgentState;
  statusText: string;        // 'Reasoning…', 'Sharing', 'Agrees', 'Standby'
  index: number;             // seat index, staggers bob and blink
  hearTick?: number;         // increment to play the one-shot "perk up"
  nodTick?: number;          // increment to play the one-shot "double nod"
  gaze?: { x: number; y: number } | null; // unit vector towards whoever is speaking, or null
  dimmed?: boolean;
  selected?: boolean;
  style?: React.CSSProperties; // left/top from the table layout
  onSelect?: () => void;
}

/** Give every inline SVG instance its own ids, so gradients and clips never collide. */
function uniquifyIds(svg: string, suffix: string): string {
  const ids = Array.from(svg.matchAll(/id="([^"]+)"/g)).map(m => m[1]);
  return ids.reduce(
    (s, id) => s.split(`id="${id}"`).join(`id="${id}-${suffix}"`).split(`url(#${id})`).join(`url(#${id}-${suffix})`),
    svg,
  );
}

/** Replays a one-shot CSS class each time `tick` changes. */
function usePulse(tick: number | undefined, ms: number): boolean {
  const [on, setOn] = useState(false);
  const first = useRef(true);
  useEffect(() => {
    if (first.current) { first.current = false; return; }
    if (tick === undefined) return;
    setOn(false);
    const raf = requestAnimationFrame(() => setOn(true));   // remove then re-add, so the animation restarts
    const t = setTimeout(() => setOn(false), ms);
    return () => { cancelAnimationFrame(raf); clearTimeout(t); };
  }, [tick, ms]);
  return on;
}

/** The SVG is memoised: re-injecting innerHTML on every render restarts every animation. */
const Face = memo(function Face({ html }: { html: string }) {
  return <span className="face" aria-hidden="true" dangerouslySetInnerHTML={{ __html: html }} />;
});

export function AgentNode(p: AgentNodeProps) {
  const reduce = useReducedMotion();
  const html = useMemo(() => uniquifyIds(p.svg, `${p.agentKey}-${p.index}`), [p.svg, p.agentKey, p.index]);
  const hear = usePulse(p.hearTick, 700);
  const nod = usePulse(p.nodTick, 950);

  // the class names must match the stylesheet exactly; keep them as literal strings (Tailwind purge-safe)
  const cls = [
    'node',
    p.state === 'thinking' && 'thinking',
    p.state === 'speaking' && 'speaking',
    p.state === 'agreed' && 'agreed',
    p.state === 'standby' && 'standby',
    hear && 'hear',
    nod && 'nod',
    p.dimmed && 'dim',
    p.selected && 'sel',
  ].filter(Boolean).join(' ');

  // gaze is expressed in SVG user units: the face is drawn on a 1024 grid and scaled, so ±30 / ±22 reads as a few pixels
  const vars = {
    '--c': p.color,
    '--d': `${(-p.index * 0.63).toFixed(2)}s`,
    '--bd': `${(p.index * 0.8 + 0.4).toFixed(2)}s`,
    '--gx': p.gaze ? `${(p.gaze.x * 30).toFixed(1)}px` : '0px',
    '--gy': p.gaze ? `${(p.gaze.y * 22).toFixed(1)}px` : '0px',
  } as React.CSSProperties;

  return (
    // framer-motion only on the OUTER element, and only OPACITY: .node uses a CSS transform
    // (translate(-50%, -32px)) to seat itself, and any framer x / y / scale here would overwrite it.
    <motion.button
      type="button"
      className={cls}
      style={{ ...p.style, ...vars }}
      initial={reduce ? false : { opacity: 0 }}
      animate={{ opacity: p.dimmed ? 0.35 : 1 }}
      transition={{ duration: 0.35, ease: [0.2, 0.7, 0.2, 1] }}
      onClick={p.onSelect}
      aria-label={`${p.name} agent, ${p.statusText}. Show only its messages.`}
    >
      {/* .av carries the CSS bob; nothing from framer-motion touches it */}
      <span className="av">
        <span className="halo" />
        <span className="spin" />
        <span className="orbit" aria-hidden="true">
          <i style={{ '--a': '0deg' } as React.CSSProperties} />
          <i style={{ '--a': '-28deg' } as React.CSSProperties} />
          <i style={{ '--a': '-52deg' } as React.CSSProperties} />
        </span>
        <Face html={html} />
        <AnimatePresence>
          {p.state === 'agreed' && (
            <motion.span
              className="ok-badge"
              initial={reduce ? false : { scale: 0 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0 }}
              transition={{ type: 'spring', stiffness: 500, damping: 18 }}
            >
              <svg viewBox="0 0 12 12" fill="none" stroke="#fff" strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round">
                <path d="M2.5 6.3l2.3 2.2 4.7-5" />
              </svg>
            </motion.span>
          )}
        </AnimatePresence>
      </span>
      <span className="nm">{p.name}</span>
      <span className="st">{p.statusText}</span>
    </motion.button>
  );
}
export default AgentNode;

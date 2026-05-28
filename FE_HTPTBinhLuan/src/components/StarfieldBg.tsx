export function StarfieldBg() {
  const particles = Array.from({ length: 60 }, (_, i) => {
    const x = (i * 137.5) % 100;
    const y = (i * 53.7) % 100;
    const delay = (i % 9) * 0.6;
    const dur = 6 + (i % 5);
    const size = (i % 3) + 1;
    return { x, y, delay, dur, size, key: i };
  });

  const streaks = [
    { top: "12%", delay: "0s", dur: "9s" },
    { top: "38%", delay: "3s", dur: "11s" },
    { top: "62%", delay: "6s", dur: "10s" },
    { top: "85%", delay: "1.5s", dur: "12s" },
  ];

  return (
    <div className="pointer-events-none fixed inset-0 -z-0 overflow-hidden bg-background">
      {/* Deep gradient base */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_oklch(0.2_0.06_240/0.8),_transparent_60%),radial-gradient(ellipse_at_bottom,_oklch(0.18_0.08_270/0.6),_transparent_60%)]" />

      {/* Perspective grid floor */}
      <div className="cyber-grid-floor" />
      {/* Perspective grid ceiling */}
      <div className="cyber-grid-ceiling" />

      {/* Pulsing glow orbs */}
      <div className="glow-orb glow-orb-1" />
      <div className="glow-orb glow-orb-2" />
      <div className="glow-orb glow-orb-3" />

      {/* Light streaks */}
      {streaks.map((s, i) => (
        <span
          key={i}
          className="light-streak"
          style={{ top: s.top, animationDelay: s.delay, animationDuration: s.dur }}
        />
      ))}

      {/* Floating neon particles */}
      {particles.map((p) => (
        <span
          key={p.key}
          className="neon-particle"
          style={{
            left: `${p.x}%`,
            top: `${p.y}%`,
            width: p.size,
            height: p.size,
            animationDelay: `${p.delay}s`,
            animationDuration: `${p.dur}s`,
          }}
        />
      ))}

      {/* Scanlines overlay */}
      <div className="scanlines" />
      {/* Vignette */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_transparent_40%,_oklch(0.08_0.02_240/0.85)_100%)]" />
    </div>
  );
}

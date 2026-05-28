import { Hash } from "lucide-react";

interface KeywordsProps {
  keywords: Array<[string, number]>;
}

export function Keywords({ keywords }: KeywordsProps) {
  if (!keywords || keywords.length === 0) return null;

  const maxCount = keywords.length > 0 ? keywords[0][1] : 1;
  const kwList1 = keywords.slice(0, 6).map((k, i) => ({
    label: k[0],
    value: k[1],
    max: maxCount,
    primary: i < 3
  }));
  const kwList2 = keywords.slice(6, 14).map((k, i) => ({
    label: k[0],
    value: k[1] / maxCount,
    primary: i < 2
  }));

  return (
    <section className="relative z-10 mx-auto max-w-6xl px-6 py-10">
      <h3 className="mb-5 flex items-center gap-2 text-base font-semibold">
        <Hash className="h-4 w-4 text-cyan" /> Từ khóa nổi bật
      </h3>

      <div className="grid gap-6 rounded-2xl border border-border bg-card/60 p-6 backdrop-blur md:grid-cols-2 shadow-card-soft">
        {/* Left: counts */}
        <div className="space-y-4">
          {kwList1.map((k) => (
            <div key={k.label} className="grid grid-cols-[100px_1fr_40px] items-center gap-4">
              <span className="text-sm text-muted-foreground truncate">{k.label}</span>
              <div className="relative h-3 overflow-hidden rounded-full bg-input">
                <div
                  className="h-full rounded-full transition-all"
                  style={{
                    width: `${(k.value / k.max) * 100}%`,
                    background: k.primary ? "var(--cyan)" : "oklch(0.55 0.18 250)",
                    boxShadow: k.primary ? "0 0 12px var(--cyan)" : "none",
                  }}
                />
              </div>
              <span className="text-right text-sm font-semibold">{k.value}</span>
            </div>
          ))}
        </div>

        {/* Right: horizontal sorted bars */}
        <div className="space-y-3 border-l border-border/60 pl-6">
          {kwList2.length === 0 ? (
            <div className="text-center text-sm text-muted-foreground py-10">Không đủ từ khóa phụ để hiển thị.</div>
          ) : (
            kwList2.map((k) => (
              <div key={k.label} className="grid grid-cols-[80px_1fr] items-center gap-3">
                <span className="text-right text-sm text-muted-foreground truncate">{k.label}</span>
                <div className="relative h-3 overflow-hidden rounded-full bg-transparent">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${k.value * 100}%`,
                      background: k.primary ? "var(--cyan)" : "oklch(0.5 0.15 250)",
                      boxShadow: k.primary ? "0 0 12px var(--cyan)" : "none",
                    }}
                  />
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </section>
  );
}


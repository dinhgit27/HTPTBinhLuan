import { Sparkles } from "lucide-react";

export function BrandLogo({ size = 40 }: { size?: number }) {
  return (
    <div
      className="flex items-center justify-center rounded-xl border border-cyan/40 bg-card shadow-glow"
      style={{ width: size, height: size }}
    >
      <Sparkles className="text-cyan" style={{ width: size * 0.55, height: size * 0.55 }} />
    </div>
  );
}

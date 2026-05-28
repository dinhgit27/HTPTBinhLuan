import { TrendingUp } from "lucide-react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface SentimentTrendProps {
  trend: {
    bins: string[];
    positive: number[];
    negative: number[];
    neutral: number[];
  };
}

export function SentimentTrend({ trend }: SentimentTrendProps) {
  if (!trend || !trend.bins) return null;

  const chartData = trend.bins.map((bin, i) => ({
    name: bin,
    positive: trend.positive[i] || 0,
    negative: trend.negative[i] || 0,
    neutral: trend.neutral[i] || 0,
  }));

  return (
    <section className="relative z-10 mx-auto max-w-6xl px-6 py-10">
      <h3 className="mb-5 flex items-center gap-2 text-base font-semibold">
        <TrendingUp className="h-4 w-4 text-cyan" /> Xu hướng cảm xúc
      </h3>
      <div className="rounded-2xl border border-border bg-card/60 p-6 backdrop-blur shadow-card-soft">
        <div className="mb-4 text-center text-sm text-muted-foreground">
          Xu hướng cảm xúc theo thời gian
        </div>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="name" stroke="var(--muted-foreground)" fontSize={12} />
              <YAxis stroke="var(--muted-foreground)" fontSize={12} />
              <Tooltip
                contentStyle={{
                  background: "var(--popover)",
                  border: "1px solid var(--border)",
                  borderRadius: 8,
                  fontSize: 12,
                }}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="positive"
                name="Tích cực"
                stroke="var(--cyan)"
                strokeWidth={3}
                dot={{ r: 5, fill: "var(--cyan)" }}
              />
              <Line
                type="monotone"
                dataKey="negative"
                name="Tiêu cực"
                stroke="var(--negative)"
                strokeWidth={2}
                dot={{ r: 4 }}
              />
              <Line
                type="monotone"
                dataKey="neutral"
                name="Trung tính"
                stroke="var(--muted-foreground)"
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <footer className="mt-10 flex flex-col items-center gap-2 pb-10">
        <div className="flex items-center gap-2 text-sm">
          <span className="font-semibold">YouTube</span>
          <span className="font-semibold text-cyan">AI Analyzer</span>
          <span className="text-muted-foreground">Pro</span>
        </div>
        <p className="text-xs text-muted-foreground">
          Phân tích cảm xúc bình luận bằng AI • 2026
        </p>
      </footer>
    </section>
  );
}


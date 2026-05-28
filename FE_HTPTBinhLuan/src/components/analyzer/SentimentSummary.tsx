import { CheckCircle2, FileText, PieChart as PieIcon, Tag, Zap } from "lucide-react";
import { Cell, Pie, PieChart, ResponsiveContainer } from "recharts";
import { AnalysisResult } from "@/lib/api";

function Bar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="flex items-center gap-3">
      <span className="h-2 w-2 rounded-full" style={{ background: color }} />
      <span className="w-20 text-sm text-muted-foreground">{label}</span>
      <div className="relative h-2 flex-1 overflow-hidden rounded-full bg-muted">
        <div className="h-full rounded-full" style={{ width: `${value}%`, background: color }} />
      </div>
      <span className="w-12 text-right text-sm font-semibold">{value}%</span>
    </div>
  );
}

interface SentimentSummaryProps {
  results: AnalysisResult;
}

export function SentimentSummary({ results }: SentimentSummaryProps) {
  const { overall, sentiment_distribution, tags, summary_header, summary_text, badge_type } = results;

  const chartData = [
    { name: "Tích cực", value: sentiment_distribution.positive_pct, color: "var(--positive)" },
    { name: "Trung tính", value: sentiment_distribution.neutral_pct, color: "var(--neutral)" },
    { name: "Tiêu cực", value: sentiment_distribution.negative_pct, color: "var(--negative)" },
  ];

  return (
    <section className="relative z-10 mx-auto grid max-w-6xl gap-6 px-6 py-6 md:grid-cols-2">
      {/* Distribution */}
      <div className="rounded-2xl border border-border bg-card/60 p-6 backdrop-blur shadow-card-soft">
        <div className="flex items-center gap-2 text-base font-semibold">
          <PieIcon className="h-4 w-4 text-cyan" /> Phân bố cảm xúc
        </div>

        <div className="relative mx-auto mt-6 h-64 w-64">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                innerRadius={75}
                outerRadius={110}
                paddingAngle={2}
                dataKey="value"
                stroke="none"
              >
                {chartData.map((d, i) => (
                  <Cell key={i} fill={d.color} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
            <div className="text-3xl font-bold">{overall.total_comments}</div>
            <div className="text-xs text-muted-foreground">Bình luận</div>
          </div>
        </div>

        <div className="mt-6 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-sm">
          <span className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-positive" /> Tích cực{" "}
            <span className="font-semibold">{sentiment_distribution.positive_pct}%</span>
          </span>
          <span className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-negative" /> Tiêu cực{" "}
            <span className="font-semibold">{sentiment_distribution.negative_pct}%</span>
          </span>
          <span className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-neutral" /> Trung tính{" "}
            <span className="font-semibold">{sentiment_distribution.neutral_pct}%</span>
          </span>
        </div>
      </div>

      {/* Summary */}
      <div className="rounded-2xl border border-border bg-card/60 p-6 backdrop-blur shadow-card-soft">
        <div className="flex items-center gap-2 text-base font-semibold">
          <Zap className="h-4 w-4 text-yellow-400" /> Tóm tắt & Đề xuất
        </div>

        <div className="mt-5 flex gap-3 text-sm">
          <CheckCircle2 className={`mt-0.5 h-5 w-5 shrink-0 ${
            badge_type === "pos" ? "text-positive" : 
            badge_type === "neg" ? "text-negative" : 
            "text-muted-foreground"
          }`} />
          <p dangerouslySetInnerHTML={{ __html: summary_header }} />
        </div>

        <div className="mt-4 rounded-xl border border-border bg-input/60 p-4 text-sm leading-relaxed text-muted-foreground">
          {summary_text}
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          {tags.map((t) => (
            <span
              key={t}
              className="inline-flex items-center gap-1.5 rounded-lg border border-cyan/30 bg-cyan/5 px-3 py-1.5 text-xs text-cyan"
            >
              <Tag className="h-3 w-3" /> {t}
            </span>
          ))}
        </div>

        <div className="mt-5 space-y-2.5">
          <Bar label="Tích cực" value={sentiment_distribution.positive_pct} color="var(--positive)" />
          <Bar label="Tiêu cực" value={sentiment_distribution.negative_pct} color="var(--negative)" />
          <Bar label="Trung tính" value={sentiment_distribution.neutral_pct} color="var(--neutral)" />
        </div>
      </div>
    </section>
  );
}


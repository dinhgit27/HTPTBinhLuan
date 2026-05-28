import { AlertTriangle, MessageCircle } from "lucide-react";

interface PainPointItem {
  title: string;
  count: number;
  desc: string;
}

interface PainPointsProps {
  painPoints: PainPointItem[];
}

export function PainPoints({ painPoints }: PainPointsProps) {
  if (!painPoints || painPoints.length === 0) return null;

  return (
    <section className="relative z-10 mx-auto max-w-6xl px-6 py-10">
      <h3 className="flex items-center gap-2 text-base font-semibold">
        <AlertTriangle className="h-4 w-4 text-yellow-400" /> Phân tích điểm yếu (Pain-point)
      </h3>
      <p className="mt-2 max-w-3xl text-sm text-muted-foreground">
        Phân tích dựa được đưa ra nhiều nhất trong các bài bình luận tiêu cực, giúp bạn xác định
        được khu vực cần ưu tiên cải thiện.
      </p>

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        {painPoints.map((p) => (
          <div
            key={p.title}
            className="flex items-start gap-4 rounded-2xl border border-negative/30 bg-card/60 p-5 backdrop-blur"
          >
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-negative/40 bg-negative/10">
              <MessageCircle className="h-4 w-4 text-negative" />
            </div>
            <div className="flex-1">
              <div className="text-base font-semibold">{p.title}</div>
              <div className="text-xs text-muted-foreground">{p.count} lần được nhắc</div>
              <p className="mt-3 text-sm text-foreground/90 break-words">{p.desc}</p>
            </div>
            <span className="flex h-7 w-7 items-center justify-center rounded-full border border-negative/40 text-xs font-semibold text-negative">
              {p.count}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}


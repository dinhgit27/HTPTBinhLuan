import { CheckCircle2, Minus, MessageCircle, ThumbsDown, ThumbsUp, Star } from "lucide-react";
import { AnalysisResult } from "@/lib/api";

function StatCard({
  icon,
  value,
  label,
  color,
  bg,
}: {
  icon: React.ReactNode;
  value: number;
  label: string;
  color: string;
  bg: string;
}) {
  return (
    <div className="flex flex-col items-center rounded-2xl border border-border bg-card/60 p-6 backdrop-blur">
      <div className={`mb-3 flex h-12 w-12 items-center justify-center rounded-full ${bg}`}>
        {icon}
      </div>
      <div className={`text-3xl font-bold ${color}`}>{value}</div>
      <div className="mt-1 text-xs uppercase tracking-widest text-muted-foreground">{label}</div>
    </div>
  );
}

interface ScoreOverviewProps {
  results: AnalysisResult;
}

export function ScoreOverview({ results }: ScoreOverviewProps) {
  const { overall, sentiment_distribution, badge_text, badge_type, platform } = results;

  // Render các ngôi sao theo điểm (tối đa 5 sao)
  const renderStars = (rating: number) => {
    const stars = [];
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating - fullStars >= 0.5;

    for (let i = 1; i <= 5; i++) {
      if (i <= fullStars) {
        stars.push(<Star key={i} className="h-6 w-6 fill-yellow-400 text-yellow-400" />);
      } else if (i === fullStars + 1 && hasHalfStar) {
        stars.push(
          <div key={i} className="relative h-6 w-6">
            <Star className="absolute h-6 w-6 text-muted-foreground/40" />
            <div className="absolute inset-y-0 left-0 overflow-hidden" style={{ width: "50%" }}>
              <Star className="h-6 w-6 fill-yellow-400 text-yellow-400" />
            </div>
          </div>
        );
      } else {
        stars.push(<Star key={i} className="h-6 w-6 text-muted-foreground/40" />);
      }
    }
    return stars;
  };

  const getPlatformName = (p: string) => {
    switch (p.toLowerCase()) {
      case "youtube": return "YouTube";
      case "facebook": return "Facebook";
      case "tiktok": return "TikTok";
      case "shopee": return "Shopee";
      case "lazada": return "Lazada";
      case "tiki": return "Tiki";
      default: return p;
    }
  };

  return (
    <section className="relative z-10 mx-auto max-w-6xl px-6 py-12">
      <div className="flex flex-col items-center text-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-positive/15 ring-2 ring-positive/40">
          <CheckCircle2 className="h-7 w-7 text-positive" />
        </div>
        <h3 className="mt-4 text-2xl font-bold text-positive">Phân tích hoàn tất!</h3>
        <p className="mt-2 text-sm text-muted-foreground">
          Đã phân tích <span className="font-semibold text-cyan">{overall.total_comments}</span> bình luận trên{" "}
          <span className="font-semibold text-cyan">{getPlatformName(platform)}</span> bằng AI.
        </p>

        <div className="mt-10 text-xs uppercase tracking-[0.2em] text-muted-foreground">
          Tổng số điểm đánh giá
        </div>
        <div className="mt-3 text-7xl font-bold text-cyan md:text-8xl">{overall.average_score}</div>
        <div className="mt-3 flex items-center gap-1">
          {renderStars(overall.star_rating)}
        </div>
        <div className="mt-2 text-sm text-muted-foreground">
          / 10 điểm • {overall.star_rating} / 5 sao
        </div>
        <div className={`mt-5 inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm ${
          badge_type === "pos" ? "border-positive/40 bg-positive/10 text-positive" :
          badge_type === "neg" ? "border-negative/40 bg-negative/10 text-negative" :
          "border-neutral-500/40 bg-neutral-500/10 text-muted-foreground"
        }`}>
          {badge_type === "pos" && <ThumbsUp className="h-4 w-4" />}
          {badge_type === "neg" && <ThumbsDown className="h-4 w-4" />}
          {badge_type === "neu" && <Minus className="h-4 w-4" />}
          {badge_text}
        </div>
      </div>

      <div className="mt-10 grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard
          icon={<ThumbsUp className="h-5 w-5 text-positive" />}
          value={sentiment_distribution.positive}
          label="Tích cực"
          color="text-positive"
          bg="bg-positive/15 ring-1 ring-positive/40"
        />
        <StatCard
          icon={<ThumbsDown className="h-5 w-5 text-negative" />}
          value={sentiment_distribution.negative}
          label="Tiêu cực"
          color="text-negative"
          bg="bg-negative/15 ring-1 ring-negative/40"
        />
        <StatCard
          icon={<Minus className="h-5 w-5 text-muted-foreground" />}
          value={sentiment_distribution.neutral}
          label="Trung tính"
          color="text-foreground"
          bg="bg-muted ring-1 ring-border"
        />
        <StatCard
          icon={<MessageCircle className="h-5 w-5 text-cyan" />}
          value={overall.total_comments}
          label="Tổng"
          color="text-cyan"
          bg="bg-cyan/15 ring-1 ring-cyan/40"
        />
      </div>
    </section>
  );
}


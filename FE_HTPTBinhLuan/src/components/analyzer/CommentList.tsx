import { Download, MessageSquare, ThumbsUp, ThumbsDown, Minus } from "lucide-react";
import { useState } from "react";

interface CommentItem {
  comment: string;
  sentiment: "Tích cực" | "Tiêu cực" | "Trung tính";
  score: number;
  name: string;
  initials: string;
  time: string;
  likes: number;
}

interface CommentListProps {
  comments: CommentItem[];
}

const FILTERS = [
  { id: "all", label: "Tất cả", color: "var(--cyan)" },
  { id: "Tích cực", label: "Tích cực", color: "var(--positive)" },
  { id: "Tiêu cực", label: "Tiêu cực", color: "var(--negative)" },
  { id: "Trung tính", label: "Trung tính", color: "var(--neutral)" },
];

export function CommentList({ comments }: CommentListProps) {
  const [filter, setFilter] = useState("all");
  const shown = filter === "all" ? comments : comments.filter((c) => c.sentiment === filter);

  const handleDownloadCSV = () => {
    try {
      const headers = ["Name", "Time", "Likes", "Sentiment", "Score", "Comment"];
      const rows = comments.map(c => [
        `"${c.name.replace(/"/g, '""')}"`,
        `"${c.time}"`,
        c.likes,
        `"${c.sentiment}"`,
        c.score,
        `"${c.comment.replace(/"/g, '""')}"`
      ]);
      
      const csvContent = "\uFEFF" + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
      const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.setAttribute("href", url);
      link.setAttribute("download", `danh_sach_binh_luan_${Date.now()}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      console.error("Lỗi xuất file CSV:", err);
    }
  };

  return (
    <section className="relative z-10 mx-auto max-w-6xl px-6 py-10">
      <div className="rounded-2xl border border-border bg-card/60 p-6 backdrop-blur shadow-card-soft">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <h3 className="flex items-center gap-2 text-base font-semibold">
            <MessageSquare className="h-4 w-4 text-cyan" /> Chi tiết bình luận
          </h3>
          <button 
            onClick={handleDownloadCSV}
            className="flex items-center gap-2 rounded-xl border border-cyan/30 bg-cyan/5 px-4 py-2 text-sm text-cyan transition hover:bg-cyan/10 cursor-pointer"
          >
            <Download className="h-4 w-4" /> Tải báo cáo (CSV)
          </button>
        </div>

        <div className="mt-5 flex flex-wrap gap-2">
          {FILTERS.map((f) => {
            const active = filter === f.id;
            return (
              <button
                key={f.id}
                onClick={() => setFilter(f.id)}
                className={`flex items-center gap-2 rounded-full border px-4 py-1.5 text-sm transition cursor-pointer ${
                  active
                    ? "border-cyan/60 bg-cyan/10 text-cyan"
                    : "border-border bg-card text-muted-foreground hover:text-foreground"
                }`}
              >
                <span className="h-1.5 w-1.5 rounded-full" style={{ background: f.color }} />
                {f.label}
              </button>
            );
          })}
        </div>

        <p className="mt-4 text-xs text-muted-foreground">
          Hiển thị {shown.length} / {comments.length} bình luận
        </p>

        <div className="mt-4 overflow-hidden rounded-xl border border-border">
          <div className="grid grid-cols-[1fr_120px_80px] gap-4 border-b border-border bg-input/40 px-5 py-3 text-xs uppercase tracking-wider text-muted-foreground">
            <span>Bình luận</span>
            <span>Cảm xúc</span>
            <span className="text-right">Điểm</span>
          </div>
          <div className="max-h-[500px] overflow-y-auto divide-y divide-border/60">
            {shown.length === 0 ? (
              <div className="text-center py-10 text-muted-foreground">Không có bình luận nào cho bộ lọc này.</div>
            ) : (
              shown.map((c, i) => (
                <div
                  key={i}
                  className="grid grid-cols-[1fr_120px_80px] items-center gap-4 px-5 py-4 transition hover:bg-accent/30"
                >
                  <div className="flex gap-3">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-border bg-input text-xs font-semibold text-muted-foreground">
                      {c.initials}
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <span className="font-medium text-foreground">{c.name}</span>
                        <span>•</span>
                        <span>{c.time}</span>
                        <span>•</span>
                        <span>{c.likes} lượt thích</span>
                      </div>
                      <p className="mt-1 text-sm text-foreground/90 break-words">{c.comment}</p>
                    </div>
                  </div>
                  <div className="flex items-center justify-start">
                    {c.sentiment === "Tích cực" && (
                      <span className="inline-flex items-center gap-1.5 rounded-lg border border-positive/40 bg-positive/10 px-3 py-1.5 text-xs text-positive">
                        <ThumbsUp className="h-3 w-3" /> Tích cực
                      </span>
                    )}
                    {c.sentiment === "Tiêu cực" && (
                      <span className="inline-flex items-center gap-1.5 rounded-lg border border-negative/40 bg-negative/10 px-3 py-1.5 text-xs text-negative">
                        <ThumbsDown className="h-3 w-3" /> Tiêu cực
                      </span>
                    )}
                    {c.sentiment === "Trung tính" && (
                      <span className="inline-flex items-center gap-1.5 rounded-lg border border-neutral-500/40 bg-neutral-500/10 px-3 py-1.5 text-xs text-muted-foreground">
                        <Minus className="h-3 w-3" /> Trung tính
                      </span>
                    )}
                  </div>
                  <div className={`text-right text-lg font-bold ${
                    c.sentiment === "Tích cực" ? "text-positive" :
                    c.sentiment === "Tiêu cực" ? "text-negative" :
                    "text-muted-foreground"
                  }`}>{c.score}</div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </section>
  );
}


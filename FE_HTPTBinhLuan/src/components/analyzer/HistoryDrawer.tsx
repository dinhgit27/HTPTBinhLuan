import { useEffect, useState } from "react";
import { X, RefreshCw, AlertCircle, Calendar, Link as LinkIcon, Star } from "lucide-react";
import { getHistory, HistoryRecord } from "@/lib/api";
import { toast } from "sonner";

interface HistoryDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectHistory: (url: string) => void;
}

export function HistoryDrawer({ isOpen, onClose, onSelectHistory }: HistoryDrawerProps) {
  const [records, setRecords] = useState<HistoryRecord[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      const fetchUserHistory = async () => {
        setIsLoading(true);
        setError(null);
        try {
          const data = await getHistory();
          setRecords(data);
        } catch (err: any) {
          setError(err.message || "Không thể tải lịch sử!");
        } finally {
          setIsLoading(false);
        }
      };
      fetchUserHistory();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const formatDate = (isoString: string) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleString("vi-VN", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return isoString;
    }
  };

  const getPlatformIcon = (platform: string) => {
    const p = platform.toLowerCase();
    if (p === "youtube") return "📺";
    if (p === "facebook") return "👥";
    if (p === "tiktok") return "🎵";
    if (p === "shopee") return "🛍️";
    if (p === "lazada") return "📦";
    if (p === "tiki") return "🛒";
    return "🔗";
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-background/80 backdrop-blur-sm">
      {/* Backdrop area click to close */}
      <div className="absolute inset-0 cursor-default" onClick={onClose} />

      {/* Drawer Body */}
      <div className="relative z-10 flex h-full w-full max-w-md flex-col border-l border-border bg-card/95 p-6 shadow-2xl backdrop-blur-md transition-all duration-300 md:max-w-lg">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border pb-4">
          <h3 className="text-lg font-bold tracking-tight text-foreground flex items-center gap-2">
            <span>🕒</span> Lịch sử phân tích
          </h3>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-muted-foreground hover:bg-input hover:text-foreground cursor-pointer"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto py-4">
          {isLoading && (
            <div className="flex flex-col items-center justify-center py-20">
              <div className="h-10 w-10 animate-spin rounded-full border-4 border-cyan/20 border-t-cyan" />
              <p className="mt-4 text-sm text-muted-foreground">Đang tải lịch sử...</p>
            </div>
          )}

          {error && !isLoading && (
            <div className="flex items-start gap-3 rounded-xl border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
              <AlertCircle className="h-5 w-5 shrink-0" />
              <div>
                <p className="font-semibold">Lỗi tải dữ liệu</p>
                <p className="mt-1 text-xs opacity-90">{error}</p>
              </div>
            </div>
          )}

          {!isLoading && !error && records.length === 0 && (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <span className="text-4xl mb-4">📭</span>
              <p className="text-sm text-muted-foreground">Bạn chưa thực hiện phân tích nào.</p>
              <p className="mt-1 text-xs text-muted-foreground/60">Hãy bắt đầu bằng việc dán đường dẫn link ở màn hình chính!</p>
            </div>
          )}

          {!isLoading && !error && records.length > 0 && (
            <div className="space-y-4">
              {records.map((r, idx) => (
                <div
                  key={idx}
                  className="group relative flex flex-col gap-2 rounded-xl border border-border bg-input/40 p-4 transition hover:border-cyan/50 hover:bg-input/60"
                >
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-1.5 text-xs font-semibold text-cyan">
                      <span>{getPlatformIcon(r.platform)}</span>
                      <span className="uppercase">{r.platform}</span>
                    </span>
                    <div className="flex items-center gap-1 text-sm font-bold text-yellow-400">
                      <Star className="h-3.5 w-3.5 fill-yellow-400" />
                      <span>{(r.score / 2).toFixed(1)} / 5</span>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-1 text-sm text-foreground/90 font-medium break-all">
                    <LinkIcon className="h-3 w-3 text-muted-foreground shrink-0" />
                    <span className="truncate max-w-[280px] md:max-w-[340px]">{r.url}</span>
                  </div>

                  <div className="flex items-center justify-between mt-2 pt-2 border-t border-border/40">
                    <span className="flex items-center gap-1 text-xs text-muted-foreground">
                      <Calendar className="h-3.5 w-3.5" />
                      <span>{formatDate(r.timestamp)}</span>
                    </span>
                    
                    <button
                      onClick={() => onSelectHistory(r.url)}
                      className="flex items-center gap-1.5 rounded-lg bg-cyan/15 px-3 py-1.5 text-xs font-semibold text-cyan transition hover:bg-cyan/25 cursor-pointer"
                    >
                      <RefreshCw className="h-3 w-3" /> Phân tích lại
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

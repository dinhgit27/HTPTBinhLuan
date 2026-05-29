import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { StarfieldBg } from "@/components/StarfieldBg";
import { AnalyzerHeader } from "@/components/analyzer/AnalyzerHeader";
import { AnalyzerHero } from "@/components/analyzer/AnalyzerHero";
import { ScoreOverview } from "@/components/analyzer/ScoreOverview";
import { SentimentSummary } from "@/components/analyzer/SentimentSummary";
import { CommentList } from "@/components/analyzer/CommentList";
import { Keywords } from "@/components/analyzer/Keywords";
import { PainPoints } from "@/components/analyzer/PainPoints";
import { SentimentTrend } from "@/components/analyzer/SentimentTrend";
import { HistoryDrawer } from "@/components/analyzer/HistoryDrawer";
import { ProfileModal } from "@/components/analyzer/ProfileModal";
import { getStoredUser, setStoredUser, analyze, getModelStatus, UserSession, AnalysisResult, ModelStatus } from "@/lib/api";
import { toast } from "sonner";
import { Progress } from "@/components/ui/progress";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "YouTube Comment AI Analyzer Pro" },
      {
        name: "description",
        content:
          "Phân tích cảm xúc bình luận YouTube bằng AI — nhận biết nổi bật, từ khóa, điểm yếu và xu hướng theo thời gian thực.",
      },
    ],
  }),
  component: Index,
});

function Index() {
  const navigate = useNavigate();
  const [user, setUser] = useState<UserSession | null>(null);
  const [url, setUrl] = useState("https://youtu.be/7NFCMm4MRvI?si=7gt_0YLz3S0Z-pla");
  const [lang, setLang] = useState("vi");
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState<AnalysisResult | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [showProfile, setShowProfile] = useState(false);
  const [modelStatus, setModelStatus] = useState<ModelStatus | null>(null);

  // Poll AI model status mỗi 5 giây cho đến khi ready
  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
    const poll = async () => {
      const status = await getModelStatus();
      setModelStatus(status);
      if (status.ready) {
        clearInterval(interval);
      }
    };
    poll();
    interval = setInterval(poll, 5000);
    return () => clearInterval(interval);
  }, []);

  // Load user session
  useEffect(() => {
    const session = getStoredUser();
    setUser(session);
  }, []);

  const handleLogout = () => {
    setStoredUser(null);
    setUser(null);
    setResults(null);
    toast.success("Đã đăng xuất tài khoản!");
  };

  const handleAnalyze = async (overrideUrl?: string) => {
    // Kiểm tra xem người dùng đã đăng nhập chưa
    const currentUser = getStoredUser();
    if (!currentUser) {
      toast.error("Vui lòng đăng nhập trước khi sử dụng tính năng phân tích bình luận!");
      navigate({ to: "/login" });
      return;
    }

    const targetUrl = overrideUrl || url;
    if (!targetUrl) {
      toast.error("Vui lòng điền đường dẫn link!");
      return;
    }
    
    setIsLoading(true);
    setResults(null);
    setProgress(0);

    // Bắt đầu bộ đếm tiến trình giả lập
    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        if (prev < 30) return prev + 2;        // Tăng nhanh lúc đầu
        if (prev < 70) return prev + 1;        // Tăng vừa phải
        if (prev < 95) return prev + 0.35;     // Tăng chậm lại
        if (prev < 98) return prev + 0.05;     // Treo ở gần 98%
        return prev;
      });
    }, 150);
    
    try {
      const data = await analyze(targetUrl, lang);
      clearInterval(progressInterval);
      setProgress(100);
      
      // Delay nhẹ để người dùng nhìn thấy 100% hoàn thành mượt mà
      setTimeout(() => {
        setResults(data);
        toast.success("Phân tích dữ liệu thành công!");
        setIsLoading(false);
      }, 400);
    } catch (err: any) {
      clearInterval(progressInterval);
      setIsLoading(false);
      toast.error(err.message || "Không thể phân tích dữ liệu, vui lòng thử lại!");
    }
  };

  const handleSelectHistory = (historyUrl: string) => {
    setUrl(historyUrl);
    setShowHistory(false);
    // Tự động phân tích khi click từ lịch sử
    setTimeout(() => handleAnalyze(historyUrl), 100);
  };

  return (
    <main className="relative min-h-screen pb-16">
      <StarfieldBg />
      <AnalyzerHeader 
        user={user} 
        onLogout={handleLogout} 
        onOpenHistory={() => setShowHistory(true)} 
        onOpenProfile={() => setShowProfile(true)}
      />
      <AnalyzerHero 
        url={url} 
        setUrl={setUrl} 
        lang={lang} 
        setLang={setLang} 
        onAnalyze={() => handleAnalyze()} 
        isLoading={isLoading} 
      />
      
      {/* AI Status Banner */}
      {modelStatus && (
        <div
          style={{
            position: "relative",
            zIndex: 10,
            margin: "0 auto 0",
            maxWidth: 720,
            padding: "0 1.5rem",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.6rem",
              padding: "0.55rem 1rem",
              borderRadius: "0.75rem",
              fontSize: "0.8rem",
              fontWeight: 500,
              border: "1px solid",
              background:
                modelStatus.state === "ready"
                  ? "rgba(34,197,94,0.10)"
                  : modelStatus.state === "loading"
                  ? "rgba(99,102,241,0.10)"
                  : "rgba(239,68,68,0.10)",
              borderColor:
                modelStatus.state === "ready"
                  ? "rgba(34,197,94,0.35)"
                  : modelStatus.state === "loading"
                  ? "rgba(99,102,241,0.35)"
                  : "rgba(239,68,68,0.35)",
              color:
                modelStatus.state === "ready"
                  ? "#4ade80"
                  : modelStatus.state === "loading"
                  ? "#a5b4fc"
                  : "#f87171",
            }}
          >
            {/* Animated dot */}
            <span
              style={{
                width: 8,
                height: 8,
                borderRadius: "50%",
                display: "inline-block",
                flexShrink: 0,
                background:
                  modelStatus.state === "ready"
                    ? "#4ade80"
                    : modelStatus.state === "loading"
                    ? "#818cf8"
                    : "#f87171",
                animation:
                  modelStatus.state === "loading"
                    ? "pulse 1.2s ease-in-out infinite"
                    : "none",
              }}
            />
            <span style={{ flex: 1 }}>
              <strong>
                {modelStatus.state === "ready"
                  ? "AI PhoBERT sẵn sàng"
                  : modelStatus.state === "loading"
                  ? "Đang tải AI PhoBERT..."
                  : "AI không khả dụng"}
              </strong>
              {" — "}
              {modelStatus.state === "ready"
                ? "Phân tích cảm xúc chính xác cao đang được sử dụng."
                : modelStatus.state === "loading"
                ? "Vẫn có thể phân tích (dùng từ điển tạm thời). Kết quả sẽ chính xác hơn sau khi AI tải xong."
                : modelStatus.message}
            </span>
          </div>
        </div>
      )}

      {isLoading && (
        <div className="relative z-10 flex flex-col items-center justify-center py-20">
          <div className="h-16 w-16 animate-spin rounded-full border-4 border-cyan/20 border-t-cyan mb-2" />
          <h3 className="mt-4 text-xl font-semibold text-foreground">
            {modelStatus?.ready ? "Đang phân tích bằng AI PhoBERT..." : "Đang phân tích dữ liệu..."}
          </h3>
          
          {/* Thanh tiến trình phân tích */}
          <div className="mt-6 w-full max-w-md px-6 flex flex-col items-center">
            <div translate="no" className="notranslate w-full">
              <Progress value={progress} className="h-2 w-full bg-cyan/10 [&>div]:bg-cyan transition-all duration-300" />
            </div>
            <div className="mt-2 flex w-full justify-between text-xs text-muted-foreground">
              <span>Đang xử lý dữ liệu...</span>
              <span translate="no" className="notranslate font-semibold text-cyan">{Math.round(progress)}%</span>
            </div>
          </div>

          <p className="mt-4 text-sm text-muted-foreground">
            {modelStatus?.ready
              ? "AI đang xử lý hàng loạt — khoảng 15–60 giây tùy số bình luận."
              : "Đang dùng phân tích từ điển — kết quả ra ngay!"}
          </p>
        </div>
      )}

      {results && !isLoading && (
        <>
          <ScoreOverview results={results} />
          <SentimentSummary results={results} />
          <CommentList comments={results.comments_sample} />
          <Keywords keywords={results.keywords} />
          <PainPoints painPoints={results.pain_points_data} />
          <SentimentTrend trend={results.sentiment_trend} />
        </>
      )}

      <HistoryDrawer 
        isOpen={showHistory} 
        onClose={() => setShowHistory(false)} 
        onSelectHistory={handleSelectHistory} 
      />
      <ProfileModal
        isOpen={showProfile}
        onClose={() => setShowProfile(false)}
        userEmail={user?.email || ""}
      />
    </main>
  );
}


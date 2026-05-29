import { Globe, Play, Search, Loader2 } from "lucide-react";

interface AnalyzerHeroProps {
  url: string;
  setUrl: (url: string) => void;
  lang: string;
  setLang: (lang: string) => void;
  onAnalyze: () => void;
  isLoading: boolean;
}

export function AnalyzerHero({
  url,
  setUrl,
  lang,
  setLang,
  onAnalyze,
  isLoading,
}: AnalyzerHeroProps) {
  return (
    <section className="relative z-10 mx-auto flex max-w-5xl flex-col items-center px-6 pt-10 pb-16 text-center">
      <div className="relative mb-8">
        <div className="absolute inset-0 -z-10 rounded-full bg-red-500/20 blur-3xl" />
        <div className="flex h-20 w-28 items-center justify-center rounded-2xl bg-red-600 shadow-2xl">
          <Play className="h-10 w-10 fill-white text-white" />
        </div>
      </div>

      <h1 className="text-5xl font-bold tracking-tight md:text-6xl">YouTube Comment</h1>
      <h2 className="mt-2 text-5xl font-bold tracking-tight text-gradient-title md:text-6xl">
        AI Analyzer Pro
      </h2>
      <p className="mt-6 max-w-2xl text-base text-muted-foreground md:text-lg">
        Tự động nhận biết nổi bật và phân tích cảm xúc bình luận thời gian thực.
        <br />
        Đánh giá chất lượng nội dung qua góc nhìn của người dùng.
      </p>

      <div className="mt-10 flex w-full max-w-4xl flex-col items-stretch gap-3 md:flex-row">
        <div className="flex flex-1 items-center gap-3 rounded-xl border border-border bg-input px-4 py-3 transition focus-within:border-cyan/60">
          <Search className="h-4 w-4 text-muted-foreground" />
          <input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={isLoading}
            placeholder="Dán link phân tích (YouTube, Facebook, Shopee, Lazada, Tiki, TikTok)..."
            className="w-full bg-transparent text-sm text-foreground placeholder:text-muted-foreground focus:outline-none"
          />
        </div>
        <button
          onClick={() => setLang(lang === "vi" ? "en" : "vi")}
          disabled={isLoading}
          className="flex items-center justify-center gap-2 rounded-xl border border-border bg-input px-4 py-3 text-sm transition hover:border-cyan/50 cursor-pointer"
        >
          <Globe className="h-4 w-4 text-cyan" /> <span>{lang === "vi" ? "Tiếng Việt" : "Tiếng Anh/Khác"}</span>
        </button>
        <button
          onClick={onAnalyze}
          disabled={isLoading}
          className="flex items-center justify-center gap-2 rounded-xl bg-gradient-analyze px-6 py-3 text-sm font-semibold text-white shadow-lg transition hover:scale-[1.02] active:scale-100 disabled:opacity-60 disabled:hover:scale-100 cursor-pointer"
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Play className="h-4 w-4 fill-white" />
          )}
          <span>Phân tích</span>
        </button>
      </div>
    </section>
  );
}


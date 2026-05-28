import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { StarfieldBg } from "@/components/StarfieldBg";
import { BrandLogo } from "@/components/BrandLogo";
import { Eye, EyeOff, LogIn, Mail, Lock, ArrowLeft, Sparkles, UserPlus, HelpCircle } from "lucide-react";
import { login, signup, forgotPassword, setStoredUser, getStoredUser } from "@/lib/api";
import { toast } from "sonner";

export const Route = createFileRoute("/login")({
  head: () => ({
    meta: [
      { title: "Đăng nhập — YouTube Comment AI Analyzer Pro" },
      {
        name: "description",
        content: "Đăng nhập vào YouTube Comment AI Analyzer Pro để phân tích cảm xúc bình luận.",
      },
    ],
  }),
  component: LoginPage,
});

type AuthMode = "login" | "signup" | "forgot";

function LoginPage() {
  const navigate = useNavigate();
  const [mode, setMode] = useState<AuthMode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Nếu đã đăng nhập, tự động chuyển về trang chủ
  useEffect(() => {
    const user = getStoredUser();
    if (user) {
      navigate({ to: "/" });
    }
  }, [navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      if (mode === "signup") {
        if (password !== confirmPassword) {
          toast.error("Mật khẩu xác nhận không khớp!");
          setIsLoading(false);
          return;
        }
        if (password.length < 6) {
          toast.error("Mật khẩu phải chứa ít nhất 6 ký tự!");
          setIsLoading(false);
          return;
        }
        const session = await signup(email, password);
        setStoredUser(session);
        toast.success("Đăng ký tài khoản thành công!");
        navigate({ to: "/" });
      } else if (mode === "login") {
        const session = await login(email, password);
        setStoredUser(session);
        toast.success("Đăng nhập thành công!");
        navigate({ to: "/" });
      } else {
        await forgotPassword(email);
        toast.success("Đã gửi email khôi phục mật khẩu. Vui lòng kiểm tra hộp thư!");
        setMode("login");
      }
    } catch (err: any) {
      toast.error(err.message || "Đã xảy ra lỗi hệ thống!");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="relative min-h-screen overflow-hidden">
      <StarfieldBg />

      {/* Header with back button */}
      <header className="relative z-10 flex items-center justify-between px-8 py-5">
        <Link to="/" className="flex items-center gap-3 transition hover:opacity-80">
          <BrandLogo size={40} />
          <span className="text-lg font-semibold tracking-tight">
            YouTube <span className="text-cyan">AI</span>
          </span>
        </Link>
        <Link
          to="/"
          className="flex items-center gap-2 rounded-lg border border-border bg-card/60 px-4 py-2 text-sm text-muted-foreground backdrop-blur-sm transition hover:border-cyan/40 hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" /> Quay lại
        </Link>
      </header>

      {/* Centered login form */}
      <section className="relative z-10 mx-auto flex max-w-md flex-col items-center px-6 pt-8 pb-16">
        {/* Decorative top glow */}
        <div className="absolute top-0 left-1/2 -z-10 h-64 w-64 -translate-x-1/2 rounded-full bg-cyan/10 blur-[100px]" />

        {/* Logo + Title */}
        <div className="mb-8 flex flex-col items-center text-center">
          <div className="relative mb-4">
            <div className="absolute inset-0 -z-10 rounded-full bg-cyan/20 blur-2xl" />
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl border border-cyan/30 bg-card shadow-glow">
              {mode === "login" && <Sparkles className="h-8 w-8 text-cyan" />}
              {mode === "signup" && <UserPlus className="h-8 w-8 text-cyan" />}
              {mode === "forgot" && <HelpCircle className="h-8 w-8 text-cyan" />}
            </div>
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">
            {mode === "login" && "Đăng nhập"}
            {mode === "signup" && "Đăng ký"}
            {mode === "forgot" && "Quên mật khẩu"}
          </h1>
          <p className="mt-2 text-sm text-muted-foreground">
            {mode === "login" && "Đăng nhập để lưu lịch sử phân tích của bạn"}
            {mode === "signup" && "Tạo tài khoản mới để trải nghiệm đầy đủ tính năng"}
            {mode === "forgot" && "Nhập email của bạn để nhận mã khôi phục"}
          </p>
        </div>

        {/* Auth Card */}
        <div className="w-full rounded-2xl border border-border bg-card/80 p-8 shadow-card backdrop-blur-md">
          <form onSubmit={handleSubmit} className="flex flex-col gap-5">
            {/* Email field */}
            <div className="flex flex-col gap-2">
              <label className="text-sm font-medium text-foreground">Email</label>
              <div className="flex items-center gap-3 rounded-xl border border-border bg-input px-4 py-3 transition focus-within:border-cyan/60 focus-within:ring-1 focus-within:ring-cyan/30">
                <Mail className="h-4 w-4 shrink-0 text-muted-foreground" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="w-full bg-transparent text-sm text-foreground placeholder:text-muted-foreground focus:outline-none"
                  required
                />
              </div>
            </div>

            {/* Password field */}
            {mode !== "forgot" && (
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-foreground">Mật khẩu</label>
                <div className="flex items-center gap-3 rounded-xl border border-border bg-input px-4 py-3 transition focus-within:border-cyan/60 focus-within:ring-1 focus-within:ring-cyan/30">
                  <Lock className="h-4 w-4 shrink-0 text-muted-foreground" />
                  <input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full bg-transparent text-sm text-foreground placeholder:text-muted-foreground focus:outline-none"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="shrink-0 text-muted-foreground transition hover:text-foreground"
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
            )}

            {/* Confirm Password field (Sign-up only) */}
            {mode === "signup" && (
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-foreground">Xác nhận mật khẩu</label>
                <div className="flex items-center gap-3 rounded-xl border border-border bg-input px-4 py-3 transition focus-within:border-cyan/60 focus-within:ring-1 focus-within:ring-cyan/30">
                  <Lock className="h-4 w-4 shrink-0 text-muted-foreground" />
                  <input
                    type={showPassword ? "text" : "password"}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full bg-transparent text-sm text-foreground placeholder:text-muted-foreground focus:outline-none"
                    required
                  />
                </div>
              </div>
            )}

            {/* Options */}
            {mode === "login" && (
              <div className="flex items-center justify-between text-sm">
                <label className="flex items-center gap-2 text-muted-foreground">
                  <input type="checkbox" className="h-4 w-4 rounded border-border bg-input accent-cyan" defaultChecked />
                  <span>Ghi nhớ tôi</span>
                </label>
                <button
                  type="button"
                  onClick={() => setMode("forgot")}
                  className="text-cyan transition hover:text-cyan-glow hover:underline bg-transparent border-none cursor-pointer"
                >
                  Quên mật khẩu?
                </button>
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={isLoading}
              className="flex items-center justify-center gap-2 rounded-xl bg-gradient-cta px-6 py-3 text-sm font-semibold text-primary-foreground shadow-lg transition hover:scale-[1.02] active:scale-100 disabled:opacity-60 disabled:hover:scale-100"
            >
              {isLoading ? (
                <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-primary-foreground/30 border-t-primary-foreground" />
              ) : (
                <>
                  {mode === "login" && (
                    <>
                      <LogIn className="h-4 w-4" /> Đăng nhập
                    </>
                  )}
                  {mode === "signup" && (
                    <>
                      <UserPlus className="h-4 w-4" /> Đăng ký
                    </>
                  )}
                  {mode === "forgot" && "Gửi yêu cầu khôi phục"}
                </>
              )}
            </button>
          </form>

          {/* Toggle register/login links */}
          <div className="mt-6 text-center text-sm text-muted-foreground">
            {mode === "login" && (
              <>
                Chưa có tài khoản?{" "}
                <button
                  onClick={() => setMode("signup")}
                  className="font-medium text-cyan transition hover:text-cyan-glow hover:underline bg-transparent border-none cursor-pointer"
                >
                  Đăng ký ngay
                </button>
              </>
            )}
            {mode === "signup" && (
              <>
                Đã có tài khoản?{" "}
                <button
                  onClick={() => setMode("login")}
                  className="font-medium text-cyan transition hover:text-cyan-glow hover:underline bg-transparent border-none cursor-pointer"
                >
                  Đăng nhập ngay
                </button>
              </>
            )}
            {mode === "forgot" && (
              <button
                onClick={() => setMode("login")}
                className="font-medium text-cyan transition hover:text-cyan-glow hover:underline bg-transparent border-none cursor-pointer"
              >
                Quay lại đăng nhập
              </button>
            )}
          </div>
        </div>

        {/* Footer decorative text */}
        <p className="mt-8 text-center text-xs text-muted-foreground/60">
          YouTube Comment AI Analyzer Pro — Phân tích cảm xúc bình luận bằng AI
        </p>
      </section>
    </main>
  );
}


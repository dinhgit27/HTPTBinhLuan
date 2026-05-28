import { History, LogIn, LogOut, User } from "lucide-react";
import { Link } from "@tanstack/react-router";
import { BrandLogo } from "../BrandLogo";
import { UserSession } from "@/lib/api";
import { toast } from "sonner";

interface AnalyzerHeaderProps {
  user: UserSession | null;
  onLogout: () => void;
  onOpenHistory: () => void;
}

export function AnalyzerHeader({ user, onLogout, onOpenHistory }: AnalyzerHeaderProps) {
  const handleHistoryClick = () => {
    if (!user) {
      toast.error("Vui lòng đăng nhập để xem lịch sử!");
      return;
    }
    onOpenHistory();
  };

  return (
    <header className="relative z-10 flex items-center justify-between px-8 py-5">
      <div className="flex items-center gap-3">
        <BrandLogo size={40} />
        <span className="text-lg font-semibold tracking-tight">
          YouTube <span className="text-cyan">AI</span>
        </span>
      </div>
      <nav className="flex items-center gap-4 text-sm text-muted-foreground md:gap-6">
        <button 
          onClick={handleHistoryClick}
          className="flex items-center gap-2 transition hover:text-foreground cursor-pointer"
        >
          <History className="h-4 w-4" /> Lịch sử
        </button>
        
        {user ? (
          <div className="flex items-center gap-3 md:gap-4">
            <div className="hidden items-center gap-1.5 text-xs text-muted-foreground md:flex">
              <User className="h-3.5 w-3.5 text-cyan" />
              <span>{user.email}</span>
            </div>
            <button
              onClick={onLogout}
              className="flex items-center gap-2 rounded-lg border border-border bg-card/40 px-3 py-1.5 text-xs text-muted-foreground backdrop-blur-sm transition hover:border-red-500/40 hover:text-red-400 cursor-pointer"
            >
              <LogOut className="h-3 w-3" /> Đăng xuất
            </button>
          </div>
        ) : (
          <Link
            to="/login"
            className="flex items-center gap-2 transition hover:text-foreground"
          >
            <LogIn className="h-4 w-4" /> Đăng nhập
          </Link>
        )}
      </nav>
    </header>
  );
}


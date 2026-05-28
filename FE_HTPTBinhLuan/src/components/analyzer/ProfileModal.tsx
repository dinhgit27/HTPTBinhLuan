import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import {
  getUserProfile,
  disconnectTelegram,
  updateTelegramSettings,
  UserProfile,
} from "@/lib/api";
import { User, Send, CheckCircle, RefreshCw, Power, Info, HelpCircle } from "lucide-react";

interface ProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
  userEmail: string;
}

export function ProfileModal({ isOpen, onClose, userEmail }: ProfileModalProps) {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(false);
  const [updating, setUpdating] = useState(false);

  const fetchProfile = async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const data = await getUserProfile();
      setProfile(data);
    } catch (err: any) {
      console.error(err);
      if (!silent) {
        toast.error(err.message || "Không thể tải thông tin cá nhân");
      }
    } finally {
      if (!silent) setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchProfile();
    }
  }, [isOpen]);

  const handleDisconnect = async () => {
    if (!confirm("Bạn có chắc chắn muốn ngắt kết nối với Telegram?")) return;
    setUpdating(true);
    try {
      await disconnectTelegram();
      toast.success("Đã ngắt kết nối Telegram thành công!");
      await fetchProfile(true);
    } catch (err: any) {
      toast.error(err.message || "Không thể ngắt kết nối Telegram");
    } finally {
      setUpdating(false);
    }
  };

  const handleToggleAutoSend = async (checked: boolean) => {
    setUpdating(true);
    try {
      await updateTelegramSettings(checked);
      toast.success(
        checked
          ? "Đã bật tự động gửi báo cáo qua Telegram!"
          : "Đã tắt tự động gửi báo cáo."
      );
      if (profile) {
        setProfile({ ...profile, auto_send_telegram: checked });
      }
    } catch (err: any) {
      toast.error(err.message || "Cập nhật cài đặt thất bại");
    } finally {
      setUpdating(false);
    }
  };

  const handleConnectClick = () => {
    if (!profile) return;
    const botUsername = "SABERlord_bot";
    const connectUrl = `https://t.me/${botUsername}?start=connect_${profile.user_id}`;
    window.open(connectUrl, "_blank");
    toast.info("Đang mở Telegram. Hãy bấm nút 'Start' trên cửa sổ chat với bot!");
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-md border-border bg-card/95 text-foreground backdrop-blur-md shadow-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-xl font-bold tracking-tight text-white">
            <User className="h-5 w-5 text-cyan" /> Trang cá nhân
          </DialogTitle>
          <DialogDescription className="text-muted-foreground text-xs">
            Quản lý tài khoản của bạn và cấu hình kết nối Telegram.
          </DialogDescription>
        </DialogHeader>

        {loading && !profile ? (
          <div className="flex flex-col items-center justify-center py-8">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-cyan/20 border-t-cyan mb-2" />
            <span className="text-xs text-muted-foreground">Đang tải thông tin...</span>
          </div>
        ) : profile ? (
          <div className="space-y-5 pt-2">
            {/* Account Details Card */}
            <div className="rounded-xl border border-border bg-card/50 p-4">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-cyan/10 text-cyan">
                  <User className="h-5 w-5" />
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-white">{profile.email}</h4>
                  <p className="text-[10px] text-muted-foreground mt-0.5">
                    User ID: <span className="font-mono text-gray-400">{profile.user_id}</span>
                  </p>
                </div>
              </div>
            </div>

            {/* Telegram Integration Details */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold tracking-wider uppercase text-cyan">
                  Kết nối Telegram
                </h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => fetchProfile(true)}
                  disabled={updating}
                  className="h-7 px-2 text-[11px] text-muted-foreground hover:text-white cursor-pointer"
                >
                  <RefreshCw className={`mr-1 h-3.5 w-3.5 ${updating ? "animate-spin" : ""}`} />
                  Làm mới
                </Button>
              </div>

              {profile.telegram_chat_id ? (
                /* Connected State */
                <div className="space-y-4 rounded-xl border border-emerald-500/20 bg-emerald-950/10 p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <CheckCircle className="h-5 w-5 text-emerald-400" />
                      <div>
                        <span className="text-xs font-semibold text-emerald-400">
                          Đã liên kết thành công
                        </span>
                        <p className="text-[11px] text-muted-foreground mt-0.5">
                          Tài khoản: <span className="text-white font-medium">@{profile.telegram_username || "User"}</span> (ID: {profile.telegram_chat_id})
                        </p>
                      </div>
                    </div>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={handleDisconnect}
                      disabled={updating}
                      className="h-8 text-xs font-medium cursor-pointer"
                    >
                      <Power className="mr-1 h-3.5 w-3.5" /> Hủy kết nối
                    </Button>
                  </div>

                  <hr className="border-border/60" />

                  {/* Auto send report settings */}
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5 pr-4">
                      <label className="text-xs font-semibold text-white cursor-pointer" htmlFor="auto-send">
                        Tự động gửi báo cáo qua Telegram
                      </label>
                      <p className="text-[10px] text-muted-foreground">
                        Hệ thống sẽ tự động nhắn báo cáo phân tích AI về Telegram của bạn sau mỗi lượt phân tích trên Web.
                      </p>
                    </div>
                    <Switch
                      id="auto-send"
                      checked={profile.auto_send_telegram}
                      onCheckedChange={handleToggleAutoSend}
                      disabled={updating}
                    />
                  </div>
                </div>
              ) : (
                /* Disconnected State */
                <div className="space-y-4 rounded-xl border border-yellow-500/20 bg-yellow-950/5 p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <HelpCircle className="h-5 w-5 text-yellow-400" />
                      <div>
                        <span className="text-xs font-semibold text-yellow-400">
                          Chưa liên kết Telegram
                        </span>
                        <p className="text-[10px] text-muted-foreground mt-0.5">
                          Liên kết để nhận báo cáo hoặc gửi link trực tiếp từ Telegram!
                        </p>
                      </div>
                    </div>
                  </div>

                  <Button
                    onClick={handleConnectClick}
                    className="w-full bg-cyan text-black hover:bg-cyan-hover font-semibold py-2 rounded-lg cursor-pointer"
                  >
                    <Send className="mr-2 h-4 w-4" /> Kết nối nhanh qua Telegram
                  </Button>

                  <div className="rounded-lg bg-card/40 p-3 text-[11px] text-muted-foreground space-y-1.5 border border-border/40">
                    <div className="flex items-start gap-1 text-cyan font-semibold">
                      <Info className="h-3.5 w-3.5 shrink-0 mt-0.5" />
                      Hướng dẫn kết nối:
                    </div>
                    <ol className="list-decimal pl-4 space-y-1">
                      <li>Bấm vào nút <strong>Kết nối nhanh qua Telegram</strong> ở trên để mở chatbot.</li>
                      <li>Bấm nút <strong>Start</strong> (hoặc gõ <code className="text-cyan">/start</code>) trong cửa sổ chat với bot.</li>
                      <li>Hệ thống sẽ tự động gộp tài khoản và phản hồi xác nhận thành công.</li>
                    </ol>
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="py-8 text-center text-sm text-red-400">
            Lỗi khi tải thông tin tài khoản. Vui lòng thử lại!
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

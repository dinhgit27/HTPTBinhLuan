export const API_BASE_URL = "http://localhost:5000";

export interface UserSession {
  idToken: string;
  email: string;
  localId: string;
  refreshToken: string;
  expiresIn: string;
}

export interface AnalysisResult {
  success: boolean;
  platform: string;
  offline_mode: boolean;
  overall: {
    url: string;
    total_comments: number;
    average_score: number;
    star_rating: number;
    summary: string;
    recommendation: string;
  };
  sentiment_distribution: {
    positive: number;
    negative: number;
    neutral: number;
    positive_pct: number;
    negative_pct: number;
    neutral_pct: number;
  };
  comments_sample: Array<{
    comment: string;
    sentiment: "Tích cực" | "Tiêu cực" | "Trung tính";
    score: number;
    name: string;
    initials: string;
    time: string;
    likes: number;
  }>;
  keywords: Array<[string, number]>;
  pain_points_data: Array<{
    title: string;
    count: number;
    desc: string;
  }>;
  sentiment_trend: {
    bins: string[];
    positive: number[];
    negative: number[];
    neutral: number[];
  };
  tags: string[];
  badge_type: "pos" | "neg" | "neu";
  badge_text: string;
  summary_header: string;
  summary_text: string;
}

export interface HistoryRecord {
  email: string;
  url: string;
  platform: string;
  score: number;
  timestamp: string;
}

// Lấy thông tin user hiện tại từ localStorage
export function getStoredUser(): UserSession | null {
  if (typeof window === "undefined") return null;
  const stored = localStorage.getItem("user_session");
  if (!stored) return null;
  try {
    return JSON.parse(stored) as UserSession;
  } catch {
    return null;
  }
}

// Lưu thông tin user
export function setStoredUser(user: UserSession | null) {
  if (typeof window === "undefined") return;
  if (user) {
    localStorage.setItem("user_session", JSON.stringify(user));
  } else {
    localStorage.removeItem("user_session");
  }
}

// Đăng nhập
export async function login(email: string, password: string): Promise<UserSession> {
  const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  
  const res = await response.json();
  if (!response.ok || !res.success) {
    throw new Error(res.error || "Đăng nhập thất bại");
  }
  return res.data;
}

// Đăng ký
export async function signup(email: string, password: string): Promise<UserSession> {
  const response = await fetch(`${API_BASE_URL}/api/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  
  const res = await response.json();
  if (!response.ok || !res.success) {
    throw new Error(res.error || "Đăng ký thất bại");
  }
  return res.data;
}

// Quên mật khẩu
export async function forgotPassword(email: string): Promise<boolean> {
  const response = await fetch(`${API_BASE_URL}/api/auth/forgot-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  
  const res = await response.json();
  if (!response.ok || !res.success) {
    throw new Error(res.error || "Gửi yêu cầu reset mật khẩu thất bại");
  }
  return true;
}

// Phân tích
export async function analyze(url: string, lang: string = "vi"): Promise<AnalysisResult> {
  const user = getStoredUser();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  
  if (user?.idToken) {
    headers["Authorization"] = `Bearer ${user.idToken}`;
    headers["X-User-Email"] = user.email;
  }
  
  const response = await fetch(`${API_BASE_URL}/api/analyze`, {
    method: "POST",
    headers,
    body: JSON.stringify({ url, lang }),
  });
  
  const res = await response.json();
  if (!response.ok || !res.success) {
    throw new Error(res.error || "Phân tích thất bại");
  }
  return res as AnalysisResult;
}

// Lấy lịch sử
export async function getHistory(): Promise<HistoryRecord[]> {
  const user = getStoredUser();
  if (!user || !user.idToken) {
    throw new Error("Người dùng chưa đăng nhập");
  }
  
  const response = await fetch(`${API_BASE_URL}/api/history?email=${encodeURIComponent(user.email)}`, {
    method: "GET",
    headers: {
      "Authorization": `Bearer ${user.idToken}`,
    },
  });
  
  const res = await response.json();
  if (!response.ok || !res.success) {
    throw new Error(res.error || "Lấy lịch sử thất bại");
  }
  return res.data as HistoryRecord[];
}

// Kiểm tra trạng thái AI PhoBERT model
export interface ModelStatus {
  state: "ready" | "loading" | "error" | "idle";
  ready: boolean;
  loading: boolean;
  error: string | null;
  message: string;
}

export async function getModelStatus(): Promise<ModelStatus> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/model-status`);
    return await response.json() as ModelStatus;
  } catch {
    return { state: "error", ready: false, loading: false, error: "Không thể kết nối server", message: "Không thể kết nối server" };
  }
}

export interface UserProfile {
  email: string;
  user_id: string;
  telegram_chat_id: number | null;
  telegram_username: string | null;
  auto_send_telegram: boolean;
}

export async function getUserProfile(): Promise<UserProfile> {
  const user = getStoredUser();
  if (!user || !user.idToken) {
    throw new Error("Người dùng chưa đăng nhập");
  }
  
  const response = await fetch(`${API_BASE_URL}/api/profile?email=${encodeURIComponent(user.email)}`, {
    method: "GET",
    headers: {
      "Authorization": `Bearer ${user.idToken}`,
    },
  });
  
  const res = await response.json();
  if (!response.ok || !res.success) {
    throw new Error(res.error || "Lấy thông tin tài khoản thất bại");
  }
  return res.data as UserProfile;
}

export async function disconnectTelegram(): Promise<boolean> {
  const user = getStoredUser();
  if (!user || !user.idToken) {
    throw new Error("Người dùng chưa đăng nhập");
  }
  
  const response = await fetch(`${API_BASE_URL}/api/profile/telegram/disconnect`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${user.idToken}`,
    },
    body: JSON.stringify({ email: user.email }),
  });
  
  const res = await response.json();
  if (!response.ok || !res.success) {
    throw new Error(res.error || "Ngắt kết nối Telegram thất bại");
  }
  return true;
}

export async function updateTelegramSettings(autoSendTelegram: boolean): Promise<boolean> {
  const user = getStoredUser();
  if (!user || !user.idToken) {
    throw new Error("Người dùng chưa đăng nhập");
  }
  
  const response = await fetch(`${API_BASE_URL}/api/profile/telegram/settings`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${user.idToken}`,
    },
    body: JSON.stringify({ email: user.email, auto_send_telegram: autoSendTelegram }),
  });
  
  const res = await response.json();
  if (!response.ok || !res.success) {
    throw new Error(res.error || "Cập nhật cài đặt thất bại");
  }
  return true;
}


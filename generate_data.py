import pandas as pd
import random
import sys
import io

# Cấu hình UTF-8 cho console để in tiếng Việt và emoji không bị lỗi trên Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# =====================================================================
# YOUTUBE DATA DICTIONARY
# =====================================================================
yt_pos_subjects = ["Video", "Nhạc", "Bài hát", "Kênh này", "Nội dung", "Cách truyền đạt", "Hình ảnh", "Beat nhạc"]
yt_pos_verbs = ["rất", "cực kỳ", "vô cùng", "khá", "thật sự", "quá"]
yt_pos_adjs = ["hay", "chill", "ý nghĩa", "cuốn", "chuyên nghiệp", "bổ ích", "chất lượng", "sâu lắng", "đỉnh cao"]
yt_pos_ends = ["nha", "nhé", "luôn", "10 điểm", "❤️", "😍", "quá chừng", "mong chờ tập sau"]

yt_neg_subjects = ["Video", "Nhạc", "Âm thanh", "Nội dung", "Cách dựng phim", "Kênh này", "Quảng cáo"]
yt_neg_verbs = ["quá", "cực kỳ", "hơi", "thật sự", "rất", "quá nhiều"]
yt_neg_adjs = ["tệ", "chán", "buồn ngủ", "nhảm nhí", "ồn ào", "nhạt nhẽo", "rác", "thiếu tôn trọng người xem"]
yt_neg_ends = ["!", "😡", "phí thời gian", "cần cải thiện", "tắt đi luôn", "hụt hẫng", "chán hẳn", "thua"]

yt_special_pos = [
    "Nghe bài này xong thấy lòng bình yên đến lạ, ủng hộ kênh nhiều.",
    "Hướng dẫn chi tiết dễ hiểu, cảm ơn kênh rất nhiều nha.",
    "Dựng phim đỉnh thực sự, màu sắc nét căng, 10 điểm không có nhưng.",
    "Bật chế độ lặp lại nghe cả ngày không chán luôn á.",
    "Nội dung bổ ích, học hỏi được rất nhiều từ video này."
]
yt_special_neg = [
    "Quảng cáo chèn vào quá nhiều, trải nghiệm cực kỳ ức chế.",
    "Nội dung giật gân câu view chứ chả có giá trị gì cả.",
    "Âm thanh mic rè rè, nghe đau hết cả đầu, chán thật sự.",
    "Xin lỗi nhưng video này làm hời hợt quá, không bằng các tập trước.",
    "Nhạc nền quá to đè hết cả tiếng người nói, quá tệ."
]

# =====================================================================
# TIKTOK DATA DICTIONARY
# =====================================================================
tt_pos_subjects = ["Trend này", "Nhạc nền", "Bé này", "Chị này", "Anh này", "Điệu nhảy", "Nhan sắc", "Content"]
tt_pos_verbs = ["cực kỳ", "quá", "siêu", "rất", "vô cùng", "quá trời"]
tt_pos_adjs = ["cuốn", "xinh", "dễ thương", "mượt", "dẻo", "ngầu", "hài hước", "bánh cuốn", "chất"]
tt_pos_ends = ["á", "nha", "❤️", "🔥", "xỉu up xỉu down", "tim cho chủ thớt", "bắn tim", "xin link nhạc"]

tt_neg_subjects = ["Trend này", "Video", "Kênh", "Content", "Nhạc này", "Diễn", "Nhìn"]
tt_neg_verbs = ["quá", "hơi", "cực kỳ", "thật sự", "khá"]
tt_neg_adjs = ["nhạt", "nhảm", "đơ", "gượng gạo", "lố lăng", "nhức mắt", "vô tri", "rác", "xàm"]
tt_neg_ends = ["!", "😡", "lướt qua luôn", "hủy follow", "bớt làm trò", "chán chả buồn nói", "flop chắc"]

tt_special_pos = [
    "Xinh xỉu up xỉu down luôn á, nhảy mượt thực sự.",
    "Xin link nhạc nền với chủ thớt ơi, nghe cuốn quá đi.",
    "Content vô tri nhưng xem cười đau cả bụng, ủng hộ nha.",
    "Đã thả tim và follow, làm thêm nhiều clip nữa nhé bạn.",
    "Nhìn thần thái đỉnh thực sự, lướt qua phải dừng lại coi luôn."
]
tt_special_neg = [
    "Content ngày càng lố lăng và nhảm nhí, hủy follow gấp.",
    "Nhảy đơ như khúc gỗ mà cũng lên xu hướng được, chịu thật.",
    "Diễn gượng gạo quá xem mà ngại giùm luôn á.",
    "Nhạc ghép chả ăn nhập gì với video cả, lướt qua luôn.",
    "Bắt chước người khác mà làm tệ hơn nhiều, flop thôi."
]

# =====================================================================
# SHOPEE DATA DICTIONARY
# =====================================================================
sp_pos_subjects = ["Sản phẩm", "Chất lượng", "Đóng gói", "Giao hàng", "Shop", "Chất vải", "Màu sắc", "Giá cả"]
sp_pos_verbs = ["rất", "cực kỳ", "siêu", "khá", "vô cùng", "thật sự"]
sp_pos_adjs = ["tốt", "đẹp", "chắc chắn", "nhanh", "nhiệt tình", "đáng tiền", "xịn xò", "thơm", "chuẩn form"]
sp_pos_ends = ["nha", "nhé", "luôn", "5 sao", "ủng hộ tiếp", "❤️", "chúc shop đắt hàng", "ưng bụng"]

sp_neg_subjects = ["Sản phẩm", "Chất vải", "Đóng gói", "Giao hàng", "Shop", "Thái độ", "Kích thước", "Đế giày"]
sp_neg_verbs = ["quá", "hơi", "rất", "cực kỳ", "thật sự", "hoàn toàn"]
sp_neg_adjs = ["tệ", "mỏng", "rách", "chậm", "khó chịu", "đắt", "nhỏ", "bẩn", "lỗi", "khác hình"]
sp_neg_ends = ["!", "😡", "phí tiền", "thất vọng", "không mua nữa", "né gấp nha", "lừa đảo", "trả hàng gấp"]

sp_special_pos = [
    "Giao hàng nhanh siêu cấp tốc, đóng gói cẩn thận 2 lớp chống sốc.",
    "Chất lượng sản phẩm tuyệt vời, vải dày dặn mặc cực thích nha.",
    "Shop tư vấn size nhiệt tình dễ thương, sẽ ủng hộ thêm nhiều lần.",
    "Đáng tiền cực kỳ, săn được đợt sale giá rẻ mà hàng nhận xịn xò lắm.",
    "Nhận hàng ưng bụng dã man, thơm phức luôn, cho shop 5 sao!"
]
sp_special_neg = [
    "Đóng gói hời hợt làm hộp móp méo, sản phẩm bên trong bị trầy xước.",
    "Giao sai mẫu sai màu, nhắn tin hoàn hàng thì shop không thèm rep.",
    "Vải mỏng dính như tờ giấy, đường chỉ may lỗi tùm lum, thất vọng.",
    "Đợi giao hàng mất hơn 10 ngày mà nhận về sản phẩm lỗi, phí tiền.",
    "Lừa đảo nha mọi người, hàng nhận về không giống mô tả tí nào cả."
]

# =====================================================================
# FACEBOOK DATA DICTIONARY
# =====================================================================
fb_pos_subjects = ["Bài viết", "Thông tin", "Quan điểm", "Admin", "Hình ảnh", "Chia sẻ", "Câu chuyện", "Nội dung"]
fb_pos_verbs = ["rất", "cực kỳ", "vô cùng", "thật sự", "quá"]
fb_pos_adjs = ["hay", "ý nghĩa", "chuẩn", "hữu ích", "chính xác", "cảm động", "tuyệt vời", "thực tế"]
fb_pos_ends = ["luôn", "nhé", "❤️", "👍", "chia sẻ ngay", "like mạnh", "thả tim", "đọc mà thấm"]

fb_neg_subjects = ["Bài viết", "Nguồn tin", "Quan điểm", "Admin", "Lập luận", "Cách hành văn", "Nội dung"]
fb_neg_verbs = ["quá", "hơi", "cực kỳ", "thật sự", "quá phiến diện"]
fb_neg_adjs = ["tệ", "chán", "nhảm", "sai lệch", "thiếu căn cứ", "toxic", "một chiều", "câu tương tác"]
fb_neg_ends = ["!", "😡", "hủy theo dõi", "bớt xàm lại", "report trang", "chán chả buồn nói", "block luôn"]

fb_special_pos = [
    "Bài viết chia sẻ thông tin rất hữu ích, cảm ơn admin nhiều.",
    "Quan điểm rất thực tế và sâu sắc, đọc mà thấm từng câu chữ.",
    "Câu chuyện cảm động quá, thả tim và chia sẻ ngay cho bạn bè.",
    "Ủng hộ góc nhìn của tác giả, cực kỳ khách quan và văn minh.",
    "Like mạnh cho trang, luôn mang lại những nội dung chất lượng thế này."
]
fb_special_neg = [
    "Thông tin sai lệch thiếu căn cứ mà cũng đăng lên câu tương tác, chán.",
    "Lập luận cực kỳ phiến diện và một chiều, mang tính chất kích động.",
    "Trang dạo này viết bài nhảm nhí và toxic quá, hủy theo dõi gấp.",
    "Hành văn lủng củng, giật tít câu view rẻ tiền chứ nội dung rỗng tuếch.",
    "Không thể đồng ý với quan điểm này, quá áp đặt và thiếu tôn trọng."
]

# =====================================================================
# GENERATION ENGINE
# =====================================================================
def generate_platform_csv(filename, pos_subj, pos_verb, pos_adj, pos_end, spec_pos,
                           neg_subj, neg_verb, neg_adj, neg_end, spec_neg, total_records=1000):
    data = []
    
    # 50% positive
    pos_count = total_records // 2
    for _ in range(int(pos_count * 0.8)):
        sentence = f"{random.choice(pos_subj)} {random.choice(pos_verb)} {random.choice(pos_adj)} {random.choice(pos_end)}"
        data.append([sentence, 1])
    for _ in range(int(pos_count * 0.2)):
        data.append([random.choice(spec_pos), 1])
        
    # 50% negative
    neg_count = total_records - pos_count
    for _ in range(int(neg_count * 0.8)):
        sentence = f"{random.choice(neg_subj)} {random.choice(neg_verb)} {random.choice(neg_adj)} {random.choice(neg_end)}"
        data.append([sentence, 0])
    for _ in range(int(neg_count * 0.2)):
        data.append([random.choice(spec_neg), 0])
        
    # Shuffle and save
    random.shuffle(data)
    df = pd.DataFrame(data, columns=['BinhLuan', 'Nhan'])
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"✅ Đã tạo thành công file '{filename}' với {len(df)} dòng dữ liệu ngẫu nhiên!")

# Generate all four files
if __name__ == "__main__":
    print("🚀 Đang khởi động hệ thống sinh dữ liệu đa nền tảng...")
    
    generate_platform_csv(
        'binh_luan_youtube.csv',
        yt_pos_subjects, yt_pos_verbs, yt_pos_adjs, yt_pos_ends, yt_special_pos,
        yt_neg_subjects, yt_neg_verbs, yt_neg_adjs, yt_neg_ends, yt_special_neg,
        total_records=1000
    )
    
    generate_platform_csv(
        'binh_luan_tiktok.csv',
        tt_pos_subjects, tt_pos_verbs, tt_pos_adjs, tt_pos_ends, tt_special_pos,
        tt_neg_subjects, tt_neg_verbs, tt_neg_adjs, tt_neg_ends, tt_special_neg,
        total_records=1000
    )
    
    generate_platform_csv(
        'binh_luan_shopee.csv',
        sp_pos_subjects, sp_pos_verbs, sp_pos_adjs, sp_pos_ends, sp_special_pos,
        sp_neg_subjects, sp_neg_verbs, sp_neg_adjs, sp_neg_ends, sp_special_neg,
        total_records=1000
    )
    
    generate_platform_csv(
        'binh_luan_facebook.csv',
        fb_pos_subjects, fb_pos_verbs, fb_pos_adjs, fb_pos_ends, fb_special_pos,
        fb_neg_subjects, fb_neg_verbs, fb_neg_adjs, fb_neg_ends, fb_special_neg,
        total_records=1000
    )
    
    generate_platform_csv(
        'binh_luan_lazada.csv',
        sp_pos_subjects, sp_pos_verbs, sp_pos_adjs, sp_pos_ends, sp_special_pos,
        sp_neg_subjects, sp_neg_verbs, sp_neg_adjs, sp_neg_ends, sp_special_neg,
        total_records=1000
    )
    
    generate_platform_csv(
        'binh_luan_tiki.csv',
        sp_pos_subjects, sp_pos_verbs, sp_pos_adjs, sp_pos_ends, sp_special_pos,
        sp_neg_subjects, sp_neg_verbs, sp_neg_adjs, sp_neg_ends, sp_special_neg,
        total_records=1000
    )
    
    print("\n🎉 Toàn bộ dữ liệu dự phòng đa nền tảng đã được tạo hoàn tất!")
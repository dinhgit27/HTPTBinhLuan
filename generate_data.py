import pandas as pd
import random

# Tập từ vựng Tích cực
pos_subjects = ["Sản phẩm", "Nhạc", "Video", "Dịch vụ", "App", "Giao diện", "Đồ ăn", "Thái độ nhân viên", "Chất lượng"]
pos_verbs = ["rất", "cực kỳ", "vô cùng", "khá", "thật sự", "quá"]
pos_adjs = ["tuyệt vời", "hay", "chill", "mượt mà", "tốt", "đáng tiền", "xịn xò", "chuyên nghiệp", "hữu ích", "ưng ý"]
pos_ends = ["nha", "nhé", "luôn", "10 điểm", "❤", "😍", "quá chừng", "đỉnh cao"]

# Tập từ vựng Tiêu cực
neg_subjects = ["Hàng", "Nhạc", "Video", "Dịch vụ", "Ứng dụng", "Đóng gói", "Chăm sóc khách hàng", "Trải nghiệm"]
neg_verbs = ["quá", "cực kỳ", "hơi", "thật sự", "rất", "hoàn toàn"]
neg_adjs = ["tệ", "chán", "buồn ngủ", "lag", "rởm", "đắt", "thất vọng", "kém", "nhảm nhí", "ồn ào"]
neg_ends = ["!", "😡", "phí tiền", "không bao giờ quay lại", "cần xem lại", "tẩy chay", "chán hẳn", "thua"]

# Tập các câu đặc thù (nguyên câu)
special_pos = [
    "Giao hàng nhanh gọn lẹ, shipper nhiệt tình.",
    "Nghe bài này xong thấy lòng bình yên đến lạ.",
    "Sẽ ủng hộ shop thêm nhiều lần nữa.",
    "Hướng dẫn chi tiết dễ hiểu, cảm ơn kênh.",
    "Vừa nhận hàng là phải vote ngay 5 sao."
]
special_neg = [
    "Mới dùng 2 ngày đã hỏng, làm ăn chán thật sự.",
    "Giao sai màu, nhắn tin không ai trả lời.",
    "Quảng cáo chèn vào quá nhiều, bực mình.",
    "Xin lỗi nhưng tôi không thể chấp nhận chất lượng này.",
    "Cập nhật xong lỗi tùm lum, xin trả lại bản cũ."
]

data = []

# Sinh 500 câu Tích cực
for _ in range(400):
    sentence = f"{random.choice(pos_subjects)} {random.choice(pos_verbs)} {random.choice(pos_adjs)} {random.choice(pos_ends)}"
    data.append([sentence, 1])
for _ in range(100):
    data.append([random.choice(special_pos), 1])

# Sinh 500 câu Tiêu cực
for _ in range(400):
    sentence = f"{random.choice(neg_subjects)} {random.choice(neg_verbs)} {random.choice(neg_adjs)} {random.choice(neg_ends)}"
    data.append([sentence, 0])
for _ in range(100):
    data.append([random.choice(special_neg), 0])

# Xáo trộn dữ liệu (Shuffle) để tránh việc mô hình học theo thứ tự
random.shuffle(data)

# Xuất ra file CSV
df = pd.DataFrame(data, columns=['BinhLuan', 'Nhan'])
df.to_csv('binh_luan_youtube.csv', index=False, encoding='utf-8-sig')

print(f"✅ Đã tạo thành công file 'binh_luan_youtube.csv' với {len(df)} dòng dữ liệu ngẫu nhiên!")
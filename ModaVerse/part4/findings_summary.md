# ModaVerse — Tổng hợp phát hiện chính (Phần 4)

Nguồn: Part 1 (làm sạch, 41,576 sản phẩm / 6 danh mục), Part 2 (mô tả & chẩn đoán), Part 3 (dự đoán — Random Forest, XGBoost, SVR-RBF).

---

## 1. Tổng quan danh mục

| Danh mục | Tổng quantity_sold | Giá TB (VND) | Discount TB | % có brand | % có video | % ế (sold=0) |
|---|---:|---:|---:|---:|---:|---:|
| fashion_accessories | **253,418** | 81,942 | 4.6% | 19.6% | 8.6% | 52.1% |
| women_shoes | 131,189 | 284,225 | 6.6% | 28.3% | 9.7% | 46.6% |
| backpacks_suitcases | 113,250 | 497,302 | 6.2% | 32.4% | 11.6% | 48.4% |
| men_bags | 105,548 | 581,027 | 8.6% | 32.8% | 16.8% | 58.7% |
| men_shoes | 95,197 | 372,352 | 6.5% | 27.2% | 8.9% | 47.4% |
| women_bags | 40,492 | 247,576 | 5.0% | 21.8% | 11.1% | **61.4%** |

**Con gà đẻ trứng vàng:** `fashion_accessories` — bán gấp ~1.9 lần danh mục #2, gấp ~6.3 lần danh mục thấp nhất, nhưng giá trị đơn hàng thấp nhất và ít giảm giá nhất → chiến lược "khối lượng lớn, giá trị thấp", không phải "giá trị cao".

---

## 2. Rating không phải đòn bẩy doanh số ở bất kỳ danh mục nào

- Tương quan `rating_average` ↔ `quantity_sold`: **0.01 – 0.06** ở cả 6 danh mục (gần như bằng 0).
- `rating_average` trung bình gần như **giống hệt nhau** giữa các danh mục (4.36–4.44/5) — không phân hóa.
- So sánh riêng theo yêu cầu đề bài: `men_shoes` (corr 0.022) và `fashion_accessories` (corr 0.056) — cả hai đều yếu tương đương, **không khác biệt đáng kể**.

## 3. Video — tác động trái chiều rõ rệt theo danh mục

| Danh mục | Uplift từ video |
|---|---:|
| women_bags | **+241.6%** |
| fashion_accessories | +203.3% |
| backpacks_suitcases | +175.3% |
| men_shoes | +111.6% |
| women_shoes | +35.5% |
| **men_bags** | **-16.2%** (duy nhất âm) |

`men_bags` là ngoại lệ duy nhất toàn sàn — có video lại bán **kém hơn**, dù đây cũng là danh mục đầu tư video nhiều nhất (16.8% listing có video, cao nhất toàn sàn).

## 4. Brand luôn thắng OEM — nhưng biên độ chênh lệch rất khác nhau

| Danh mục | Uplift từ brand |
|---|---:|
| **men_bags** | **+668.0%** |
| women_bags | +477.7% |
| men_shoes | +285.1% |
| backpacks_suitcases | +271.6% |
| fashion_accessories | +189.0% |
| women_shoes | +114.4% |

Không như video, brand **không đảo chiều ở danh mục nào** (6/6 dương) — nhưng mức độ dao động 114%–668%, gấp gần 6 lần giữa cao nhất/thấp nhất.

## 5. Giá trị vs. phụ thuộc giảm giá (theo giá TB / discount TB)

- **men_bags**: giá cao nhất (582k) **và** discount cao nhất (8.6%) — phải giảm giá mạnh nhất để bán được hàng giá trị cao.
- **fashion_accessories**: giá thấp nhất (82k) **và** discount thấp nhất (4.6%) — bán nhờ giá vốn rẻ, không cần khuyến mãi.
- Không danh mục nào thuộc nhóm "giá cao, ít giảm giá" (định vị thương hiệu thuần túy, không cần trợ giá).

## 6. Hai danh mục "túi xách" luôn ế nhất, và phân cực nhất

- `men_bags` (58.7% ế) và `women_bags` (61.4% ế) — cao hơn hẳn 4 danh mục còn lại (46.6–52.1%).
- `men_bags`: chỉ số cực đoan nhất toàn sàn ở mọi mặt (giá, discount, brand uplift cao nhất) nhưng **video phản tác dụng** và tỷ lệ ế cao thứ 2 — kiểu "được ăn cả, ngã về không".
- `women_bags`: khối lượng thấp nhất, ế nhiều nhất, nhưng **phần thưởng đầu tư (video, brand) lớn nhất** — cơ hội tăng trưởng rõ ràng nếu được hỗ trợ marketing.

---

## 7. Mô hình dự đoán — so sánh 3 thuật toán

Dùng bộ 7 numeric feature "ver2" (đã loại `favorite_count` — variance=0, và `original_price` — tương quan 0.975 với `price`).

| Model | RMSE (test) | R² (test) |
|---|---:|---:|
| Random Forest | 257.15 | 0.2557 |
| **XGBoost** | **256.78** | **0.2578** |
| SVR (RBF) | 285.07 | 0.0853 |

- Random Forest và XGBoost gần như ngang nhau, đều vượt trội SVR.
- SVR (kernel RBF) kém hẳn vì `quantity_sold` là dữ liệu đếm **zero-inflated cực đoan** (51.8% sản phẩm = 0, skewness 86.7) — không phù hợp với giả định "hàm mượt liên tục" của SVR. Model cây (chia không gian thành vùng rời rạc) phù hợp hơn nhiều với kiểu phân phối này.
- R² ở mức khiêm tốn (~0.26) cho cả model tốt nhất — phần lớn do đuôi phân phối quá dài (std=298 vs mean=21), một số sản phẩm "viral" chi phối phương sai.

## 8. sub_category CÓ phải yếu tố dự báo hàng đầu?

| Model | Rank sub_category | Trong top 5? |
|---|---|---|
| Random Forest | #5/12 (importance 0.013) | Sát ranh giới, có |
| XGBoost | #2/12 (importance 0.181) | Rõ ràng có |

**Top 5 yếu tố quan trọng nhất:**
- Random Forest: `review_counts` → `date_created` → `price` → `number_of_images` → `sub_category`
- XGBoost: `review_counts` → `sub_category` → `fulfillment_type` → `date_created` → `rating_average`

→ Cả 2 model đồng ý `sub_category` có vai trò thật, nhưng **luôn đứng sau** `review_counts` (và ở XGBoost là `fulfillment_type`) — chọn đúng danh mục có lợi nhưng không quyết định; **cách vận hành sản phẩm** (đăng sớm, giá đúng, đủ ảnh) mới là đòn bẩy chính.

> **Caveat quan trọng:** `review_counts` đứng đầu ở cả 2 model, nhưng đây là biến "hậu kiểm" — 55.1% sản phẩm có `review_counts` bằng **chính xác** `quantity_sold` (kiểm chứng trực tiếp trên dữ liệu), cho thấy quan hệ cơ học/định nghĩa chứ không phải đòn bẩy marketing có thể chủ động điều chỉnh trước khi bán. Yếu tố hành động được nên ưu tiên: `date_created` (đăng sớm), `price`/`discount_rate`, `number_of_images`, `fulfillment_type`, `is_branded`.

---

## 9. Đề xuất chiến lược theo danh mục (Phần 4.2)

### Giày (Nam & Nữ)
`rating_average` **không phải** yếu tố quan trọng (corr 0.01–0.02, ngược với giả định "vd: rating_average" trong đề bài) — không nên tư vấn nhà bán tập trung vào cải thiện rating. Yếu tố thật sự có ích: đăng bán sớm/liên tục (`date_created`), tối ưu giá cạnh tranh, và brand — giày nam có uplift brand rất cao (+285%). → Tư vấn nhà bán giày: ưu tiên đăng sản phẩm mới đều đặn, cạnh tranh giá, và cân nhắc hợp tác thương hiệu thay vì chăm chút rating.

### Túi xách (Nam & Nữ)
Brand là đòn bẩy mạnh nhất toàn sàn ở đây (men_bags +668%, women_bags +478%) — nên ưu tiên seller có thương hiệu, giảm tỷ trọng OEM. Về giá: men_bags cần chiến lược giá cao + discount sâu (định vị cao cấp nhưng vẫn cần khuyến mãi để chốt đơn); women_bags nên đầu tư mạnh video/nội dung (uplift +242%, cao nhất toàn sàn) để khai thác dư địa tăng trưởng dù thị trường nhỏ và tỷ lệ ế cao.

### Chiến lược chung toàn sàn
Ưu tiên theo mức độ hành động được và tác động: (1) khuyến khích seller đăng bán sớm & duy trì listing hoạt động (`date_created` là feature quan trọng thứ 2), (2) tối ưu giá/discount hợp lý theo từng phân khúc thay vì đại trà, (3) khuyến khích làm video có chọn lọc theo danh mục (không áp dụng đồng loạt — tác động ngược ở men_bags), (4) ưu tiên hợp tác thương hiệu hơn OEM trên toàn sàn. Không nên dồn toàn bộ nguồn lực chọn "danh mục đúng" — vì sub_category quan trọng nhưng không phải yếu tố quyết định hàng đầu.

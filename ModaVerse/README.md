# ModaVerse - Phân tích hiệu suất kinh doanh sản phẩm thời trang

Đề bài: [requirement.pdf](requirement.pdf) · Dữ liệu gốc: [Raw_Dataset/](Raw_Dataset) (6 file CSV theo danh mục)

## Setup môi trường (chạy 1 lần)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Mỗi lần chạy lại script ở các phần bên dưới, nhớ `source .venv/bin/activate` trước.

> **Lưu ý:** Phần 3 huấn luyện **cả 2 model** (Random Forest và XGBoost) để so
> sánh, dù đề bài chỉ yêu cầu chọn một trong hai. XGBoost cần thư viện hệ thống
> `libomp` (`brew install libomp`) mới chạy được trên macOS.

## Cấu trúc thư mục

```
Raw_Dataset/                6 file CSV gốc theo danh mục (đầu vào, không chỉnh sửa)

part1/                      Phần 1: Thu thập & Chuẩn bị dữ liệu
  01_merge_data.py            - Phần 1.1: đọc 6 CSV từ ../Raw_Dataset, gắn cột sub_category,
                                 gộp thành 1 DataFrame -> ../Merge_Datasets/merged_raw.csv
  02_clean_preprocess.py       - Phần 1.2: đọc merged_raw.csv, làm sạch (missing values,
                                 dtypes, giá lỗi, trùng lặp) + feature engineering
                                 (discount_rate, is_branded) -> ../Merge_Datasets/merged_products.csv
  output/
    cleaning_report.txt        - log các bước làm sạch, số dòng bị ảnh hưởng

Merge_Datasets/              Dữ liệu trung gian & đầu ra của Phần 1 (dùng chung cho Phần 2 & 3)
  merged_raw.csv               - đã gộp, CHƯA làm sạch (output bước 1.1)
  merged_products.csv          - đã sạch, có sub_category/discount_rate/is_branded (output bước 1.2)

part2/                       Phần 2: Phân tích Mô tả & Chẩn đoán
  analysis.py                  - đọc ../Merge_Datasets/merged_products.csv
  figures/
    01_total_quantity_sold_by_category.png     - danh mục nào là "con gà đẻ trứng vàng"
    02_price_vs_discount_quadrant.png          - giá trị cao vs. phụ thuộc giảm giá
    03_rating_vs_quantity_all_categories.png   - rating vs doanh số, toàn bộ 6 danh mục
    04_rating_vs_quantity_focus_menshoes_accessories.png  - so sánh riêng giày nam vs phụ kiện
    05_video_impact_by_category.png            - tác động của video theo danh mục
    06_brand_vs_oem_by_category.png             - brand vs OEM theo danh mục
  output/*.csv, *.txt          - bảng số liệu & correlation đằng sau mỗi chart

part3/                       Phần 3: Phân tích Dự đoán (Random Forest + XGBoost)
  train_model.py               - đọc ../Merge_Datasets/merged_products.csv
  figures/
    feature_importance_top15_random_forest.png
    feature_importance_top15_xgboost.png
    feature_importance_comparison.png   - so sánh trực tiếp top feature giữa 2 model
    model_comparison_rmse_r2.png        - so sánh RMSE & R2 giữa 2 model
  output/
    model_performance.txt                       - RMSE, R2 của từng model
    feature_importance_aggregated_<model>.csv    - importance đã gộp one-hot về biến gốc
    feature_importance_raw_onehot_<model>.csv    - importance chi tiết từng one-hot column
    interpretation_notes.txt       - trả lời câu hỏi: sub_category có phải top predictor?
                                      (2 model có thể cho câu trả lời khác nhau - xem file
                                      để biết model nào đồng ý/không đồng ý), top 5 yếu tố
                                      quan trọng nhất, kèm caveat về review_counts (biến
                                      "hậu kiểm", cần cẩn thận khi diễn giải thành chiến lược)

part4/                       Phần 4: (để trống - bạn tự làm slide & đề xuất)
```

## Cách chạy lại từ đầu

```bash
source .venv/bin/activate

cd part1 && python 01_merge_data.py && python 02_clean_preprocess.py && cd ..
cd part2 && python analysis.py && cd ..
cd part3 && python train_model.py && cd ..
```

## Kết quả chính (để tham khảo khi làm Phần 4)

- **Phần 2:** xem số liệu trong `part2/output/*.csv` và các chart tương ứng trong
  `figures/` - mỗi chart trả lời đúng 1 câu hỏi trong đề bài.
- **Phần 3:** Random Forest và XGBoost cho RMSE/R² gần như bằng nhau (R² ≈ 0.255,
  RMSE ≈ 257, so với mean quantity_sold ≈ 21, std ≈ 298 - dữ liệu rất lệch/đuôi
  dài do một số sản phẩm bán rất chạy) nhưng **bất đồng đáng chú ý** về vai trò
  của `sub_category`: Random Forest xếp hạng #6/14 (không vào top 5), còn XGBoost
  xếp hạng #2/14 (vào top 5, cùng với `fulfillment_type`). Đây là điểm cần nêu rõ
  khi trình bày - kết luận "category có quan trọng không" phụ thuộc vào model,
  chưa chốt được. Đọc `interpretation_notes.txt` để có đầy đủ caveat (đặc biệt về
  `review_counts` - biến hậu kiểm) trước khi đưa vào slide.

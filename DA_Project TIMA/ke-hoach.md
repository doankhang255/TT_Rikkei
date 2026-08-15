# Kế hoạch làm việc — DA_Project TIMA

Định hướng dựa trên yêu cầu ở `resources/task1.pdf`, `resources/task2.pdf` và kết quả profiling thực tế trên `Data/Tima raw - Tima_CRM - raw.csv` (2.383 dòng × 49 cột, mỗi dòng là **một khoản vay**, khóa chính thật sự là `LoanID`/`ID` — cả hai đều unique 100%).

## 1. Nhóm cột theo nghiệp vụ (data dictionary sơ bộ)

| Nhóm | Cột |
|---|---|
| Định danh & trạng thái khoản vay | `STT`, `ID`, `LoanID`, `application_date`, `FromDate`, `ToDate`, `Trạng thái`, `ProductCreditName`, `InterestPaymentType` |
| Tài chính khoản vay | `SoTienDKVayBanDau`, `Số tiền đăng ký vay ban đầu`, `TienGiaiNgan`, `Tiền giải ngân`, `SoTienConLai`, `Tiền gốc còn lại`, `LongestOverdue`, `NumberOfLoans`, `HasBadDebt`, `HasLatePayment` |
| Định danh khách hàng | `FullName`, `CardNumber`, `Gender`, `Birthday`, `Số điện thoại khách hàng` |
| Địa chỉ hiện tại / hộ khẩu | `CityName`, `DistrictName`, `WardName`, `Hình thức cư trú`, `Thời gian đã sống`, `Street`, `CityNameHouseHold`, `DistrictNameHouseHold`, `WardNameHouseHold` |
| Công việc & thu nhập | `JobName`, `NameCompany`, `AddressCompany`, `CityCompany`, `DistrictNameCompany`, `Salary`, `ReceiveYourIncomeSalary`, `DescriptionPositionJob` |
| Người thân tham chiếu | `RelativeFamilyName`, `FullNameFamily` |
| Tín dụng/CIC (tra cứu nợ xấu ngoài hệ thống) | `CreditInfo`, `Name`, `Address`, `CheckTime`, `Brieft` |

→ Việc cần làm trong **Task 1**: xác nhận lại 7 nhóm này với người hiểu nghiệp vụ Tima (hoặc suy luận hợp lý nếu không phỏng vấn được), viết ý nghĩa từng cột thành từ điển dữ liệu chính thức (Excel/Notion), rồi mới bắt tay làm sạch — tránh xóa nhầm cột do tưởng là "rác".

## 2. Vấn đề dữ liệu đã xác minh trên file thật (Task 2 bám vào đây)

### 2.1 Cột trùng lặp/gần trùng — cần đối chiếu trước khi gộp
Đã so khớp từng cặp cột song ngữ Việt/Anh trông giống nhau:

| Cặp cột | Kết quả đối chiếu | Hành động |
|---|---|---|
| `SoTienDKVayBanDau` ↔ `Số tiền đăng ký vay ban đầu` | Giống nhau **100%** (2.383/2.383) | Trùng lặp thật → giữ 1, xóa 1 |
| `TienGiaiNgan` ↔ `Tiền giải ngân` | Giống nhau 2.382/2.383, lệch đúng 1 dòng (250.000 vs 10.000.000) | Gần như trùng, nhưng có 1 dòng mâu thuẫn cần soát tay trước khi gộp |
| `SoTienConLai` ↔ `Tiền gốc còn lại` | **Khác nhau ở 1.674/2.383 dòng** | KHÔNG phải cột trùng — có thể là 2 mốc thời gian khác nhau (dư nợ hiện tại vs dư nợ gốc tại thời điểm snapshot). Cần hỏi nghiệp vụ, không được xóa |
| `application_date` ↔ `FromDate` | Cùng ngày nhưng khác định dạng; `application_date` có ngày **không hợp lệ** (vd `2023-02-30` — tháng 2 không có ngày 30) | Dùng `FromDate` làm nguồn ngày chính, `application_date` cần parse lại/loại dòng lỗi |

### 2.2 Giá trị thiếu / sentinel lộn xộn
- Thiếu dữ liệu nặng: `ReceiveYourIncomeSalary` thiếu 1.943/2.383 (81%), `WardName` thiếu 1.716 (72%), `CityCompany` thiếu 610 (26%), `DescriptionPositionJob` thiếu 482 (20%), `NumberOfLoans` mang giá trị sentinel `-1` ở 480 dòng (20%).
- Giá trị thiếu được biểu diễn không đồng nhất: chuỗi rỗng `''`, chuỗi `"null"`, `"NaN"`, và sentinel số `-1` cùng tồn tại tùy cột → phải quy ước 1 chuẩn duy nhất (khuyến nghị: `NaN`/null thật của pandas) trước khi tính toán, nếu không các phép đếm/trung bình sẽ sai vì `-1` bị tính như số thật.
- Nhóm `CreditInfo`, `Name`, `Address`, `Brieft`... thiếu đồng loạt ở cùng ~217-218 dòng → khả năng là các khoản vay chưa được tra cứu CIC, không phải lỗi nhập liệu — nên tạo cờ `has_cic_check` thay vì fillna vô tội vạ.

### 2.3 Định dạng không nhất quán
- **Ngày tháng**: tối thiểu 3 định dạng khác nhau trong cùng cột (`2023-02-30`, `7/28/16`, `6/29/16 0:00`), có ngày dương lịch không tồn tại → phải parse an toàn (`errors='coerce'`) và log lại các dòng lỗi thay vì crash/âm thầm sai.
- **Gender**: 4 giá trị khác kiểu cho cùng 1 ý nghĩa — `'0'`, `'1'`, `'Male'`, `''` (rỗng) → cần map về 1 chuẩn (vd `Male/Female/Unknown`).
- **Trạng thái**: 4 nhãn — `Kết thúc`, `Đang Vay`, `Đang vay xong`, `Nợ Xấu`. `"Đang Vay"` và `"Đang vay xong"` rất giống nhau về câu chữ → cần hỏi nghiệp vụ xem có phải 2 trạng thái khác nhau thật hay lỗi nhập liệu cần gộp.
- **Salary**: trộn lẫn số thuần (`7700000`), chuỗi có đơn vị (`1000$`), và cả câu chữ tiếng Anh (`"Ten thousand"`) trong cùng 1 cột số → cần rule parser riêng, không thể `astype(float)` trực tiếp.
- **Địa danh** (`Street`, tên công ty...): lẫn lộn có dấu/không dấu (`"Giải Phóng"` vs `"Phuong mai"`) → cân nhắc chuẩn hóa unicode/bỏ dấu nhất quán nếu dùng để group/join.

### 2.4 Về grain dữ liệu
- `CardNumber` (CMND/CCCD khách hàng) chỉ có 1.868 giá trị unique trong 2.383 dòng → 354 khách hàng có **nhiều hơn 1 khoản vay**. Đây là hành vi vay lặp lại bình thường, không phải trùng dòng — **không được `drop_duplicates()` theo CardNumber**, chỉ dedupe nếu toàn bộ dòng (hoặc `LoanID`) lặp y hệt.

## 3. Trình tự thực hiện đề xuất

1. **Task 1 trước, Task 2 sau** — chốt từ điển dữ liệu & KPI với "nghiệp vụ" (ở đây bạn tự đóng vai stakeholder nếu không có bộ phận để hỏi) trước khi viết code làm sạch, để không đoán sai ý nghĩa cột `SoTienConLai` vs `Tiền gốc còn lại`.
2. **Làm sạch bằng Python trước** (dễ log, dễ tái lặp, dễ review diff), theo thứ tự:
   - Đọc CSV với `encoding='utf-8-sig'`, chuẩn hóa tên cột (bỏ khoảng trắng, đặt slug không dấu cho cột kỹ thuật).
   - Chuẩn hóa mọi biến thể thiếu (`''`, `'null'`, `'NaN'`, `-1` theo từng cột cụ thể) → `NaN` thật bằng `na_values`/`replace`.
   - Parse ngày tháng bằng `pd.to_datetime(..., errors='coerce')`, tạo cột log các dòng bị coerce thành `NaT` để soát riêng (đừng xóa âm thầm).
   - Xử lý từng cặp cột trùng ở mục 2.1: drop cột trùng thật, giữ + đặt cờ cho cột mâu thuẫn/khác nghĩa.
   - Chuẩn hóa categorical: `Gender`, `Trạng thái` (map dictionary tường minh, lưu lại bảng mapping).
   - Viết parser riêng cho `Salary` (regex tách số, quy đổi `$`/chữ số viết bằng chữ về VNĐ, đặt `NaN` nếu không parse được kèm log).
   - `drop_duplicates()` chỉ theo `LoanID` (khóa thật), không theo `CardNumber`/`FullName`.
   - Xuất ra `Data/tima_clean.csv` (hoặc `.parquet`) + `Data/data_dictionary.csv` + `Data/cleaning_log.csv` (liệt kê số dòng bị sửa/loại theo từng bước, phục vụ báo cáo Task 2).
3. **Sau khi có bộ dữ liệu sạch** → nạp vào Power BI để làm báo cáo/KPI, dùng lại đúng các bước tương ứng (Power Query) như checklist trong `task2.pdf` nếu cần chỉnh thêm trong BI, nhưng phần nặng nên xử lý ở Python để có version kiểm soát được bằng git.

## 4. Đề xuất KPI & câu hỏi phân tích ban đầu (Task 1 mục 4)

- Tỷ lệ nợ xấu / nợ quá hạn theo thời gian, theo khu vực (`CityName`), theo `ProductCreditName`.
- Phân phối `LongestOverdue` theo nhóm khách hàng (nghề nghiệp, thu nhập, hình thức cư trú).
- Số khoản vay lặp lại trên 1 khách hàng (`CardNumber`) và mối liên hệ với `HasBadDebt`/`HasLatePayment`.
- Thời gian xử lý khoản vay: `ToDate - FromDate`, theo `Trạng thái`.
- Tỷ lệ khoản vay có tra cứu CIC (`has_cic_check`) và mối liên hệ với nợ xấu.

## 5. Việc cần làm tiếp theo (checklist ngắn)

- [ ] Chốt từ điển dữ liệu (mục 1) — xác nhận ý nghĩa `SoTienConLai` vs `Tiền gốc còn lại`.
- [ ] Viết script Python làm sạch theo mục 3, log lại số dòng ảnh hưởng mỗi bước.
- [ ] Xuất `tima_clean.csv` + `cleaning_log.csv` vào `Data/`.
- [ ] Dựng file/báo cáo Power BI hoặc notebook phân tích trả lời các câu hỏi ở mục 4.
- [ ] Viết báo cáo tổng hợp Task 1 + Task 2 (mô tả nghiệp vụ, từ điển dữ liệu, log làm sạch, KPI) để nộp.

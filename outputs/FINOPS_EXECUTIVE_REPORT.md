# NimbusAI — Báo Cáo Chuyên Sâu Tối Ưu Hóa Chi Phí GPU (GPU FinOps Report)

> **Khóa học**: AICB · Phase 2 · Track 2 (Infrastructure) · Day 25  
> **Dự án**: GPU FinOps Cost Optimization Workshop  
> **Học viên**: Hà Duyên Hùng  
> **Tài liệu bàn giao cho**: Ban Giám đốc & Team Kỹ thuật *NimbusAI* (Đầu vào Milestone 2)

---

## I. TỔNG QUAN HIỆU QUẢ TỐI ƯU HÓA (BASELINE VS. OPTIMIZED)

Trong bối cảnh chi phí hóa đơn GPU của NimbusAI tăng đột biến và mất kiểm soát, chúng tôi đã áp dụng khung phương pháp luận **FinOps Foundation (Inform -> Optimize -> Operate)** kết hợp đo lường hiệu suất thực tế (MFU/MBU) để tái cấu trúc toàn diện hạ tầng tính toán.

### 1. Bảng so sánh chỉ số tài chính và Unit Economics

| Chỉ số (Metrics) | Trước tối ưu (Baseline) | Sau tối ưu (Optimized) | Mức cắt giảm (% Savings) | Ý nghĩa tài chính |
|---|---|---|---|---|
| **Tổng chi phí hàng tháng** | **$27,133 / tháng** | **$14,550 / tháng** | **-46.4%** (**-$12,583/tháng**) | Tiết kiệm **~$151,000/năm** |
| **Đơn giá suy luận (`$/1M-token`)** | **$6.488 / 1M-tok** | **$1.126 / 1M-tok** | **-82.6%** | Phục vụ cùng lượng traffic với giá rẻ hơn gần 6 lần |
| **Chi phí Inference theo ngày** | $48.87 / ngày | $8.49 / ngày | -82.6% | Đòn bẩy cascade + cache + batch |
| **Chi phí Workload cố định/ngày** | $855.57 / ngày | $518.37 / ngày | -39.4% | Đòn bẩy spot + 3yr reserved |
| **Lãng phí Idle GPU** | $600 / tháng | $0 / tháng | -100.0% | Thu hồi 100% chi phí lãng phí vô ích |
| **Lãng phí do Over-provisioning** | $655 / tháng | $0 / tháng | -100.0% | Right-sizing GPU đúng năng lực tính toán |
| **Phát thải Carbon (Training)** | 1,606.3 kg CO2e/tháng | 126.8 kg CO2e/tháng | **-92.1%** | Giảm phát thải nhờ điều phối sang vùng điện sạch |

---

## II. PHÂN TÍCH CHI TIẾT 4 ĐÒN BẨY TỐI ƯU HÓA (FINOPS LEVERS)

Tổng số tiền tiết kiệm **$12,583/tháng** được cấu thành từ 4 đòn bẩy độc lập:

```
[Tổng tiết kiệm: $12,583/tháng]
 ├── Purchasing Strategy (Spot + 3yr Reserved): $10,116/tháng (80.4%)
 ├── Inference Levers (Cascade + Cache + Batch): $1,212/tháng (9.6%)
 ├── Right-Sizing Memory-Bound GPUs:           $655/tháng   (5.2%)
 └── Kill Idle GPUs:                           $600/tháng   (4.8%)
```

### 1. Đòn bẩy 1: Chiến lược Mua sắm Hạ tầng (Purchasing Strategy) — Đóng góp 80.4% ($10,116/tháng)
- **Bản chất**: Workloads huấn luyện và tinh chỉnh mô hình (`job-train-llm`, `job-train-embed`, `job-finetune`) có tính chất `interruptible=1`. Thay vì trả giá On-demand đắt đỏ, chúng tôi chuyển toàn bộ sang **Spot Instances** kết hợp cơ chế lưu checkpoint định kỳ (3% overhead, 0.5h rework penalty).
- Đối với các dịch vụ inference chạy 24/7 ổn định (`job-infer-chat`, `job-infer-rag`), hệ thống cam kết **3-Year Reserved Instances** (chiết khấu 45%, vượt xa điểm hòa vốn 55% utilization).

### 2. Đòn bẩy 2: Đòn bẩy Chi phí Inference (Cascade x Cache x Batch) — Đóng góp 9.6% ($1,212/tháng)
- **Model Cascading**: Định tuyến các câu hỏi đơn giản/phổ thông sang mô hình `small` (chi phí $0.20/$0.40 per 1M-token) thay vì dồn toàn bộ vào `large` ($3.00/$15.00 per 1M-token).
- **Prompt Caching**: Áp dụng chiết khấu 90% cho các đoạn context/system prompt được tái sử dụng nhiều lần.
- **Batch API**: Tận dụng cơ chế xử lý không đồng bộ (chiết khấu 50%) cho các tác vụ không yêu cầu thời gian thực.
- **Hiệu ứng chồng chiết khấu (Discount Stacking)**: $0.50 \times 0.10 = 0.05$ (giảm tới 95% chi phí trên mỗi token đủ điều kiện).

### 3. Đòn bẩy 3: Right-Sizing GPU dựa trên MBU & Roofline Model — Đóng góp 5.2% ($655/tháng)
- Hạ cấp các GPU bị over-provisioned (`gpu-h100-4`, `gpu-a10g-1`) sang các dòng GPU tương thích năng lực thực tế (H100 -> A100, A10G -> L4), tiết kiệm chi phí thuê theo giờ mà không làm suy giảm SLA.

### 4. Đòn bẩy 4: Xóa bỏ Lãng phí GPU Idle (Kill Idle GPUs) — Đóng góp 4.8% ($600/tháng)
- Phát hiện và tự động tắt các GPU chạy không (`gpu_util_pct < 10%`) sau khi hoàn thành training, cắt đứt ngay lập tức $20/ngày ($600/tháng) tiền "đốt" vô ích.

---

## III. HIỆN TƯỢNG "GPU-UTIL LIE" VÀ TÁC ĐỘNG TÀI CHÍNH

### 1. Tại sao `nvidia-smi` GPU-Util 98% lại là "nói dối"?
- Lệnh `nvidia-smi` chỉ đo **tỷ lệ phần trăm thời gian mà bộ xung nhịp (clock) của GPU đang ở trạng thái tích cực**, chứ **không đo lường hiệu suất thực thi phép tính (FLOPs)**.
- Khi GPU thực hiện tác vụ sinh từ (LLM Decode), mỗi token sinh ra phải nạp lại toàn bộ trọng số mô hình từ bộ nhớ HBM vào SRAM. Vì tỷ lệ tính toán trên dữ liệu nạp rất thấp (**Arithmetic Intensity ≈ 1-2 FLOP/byte**), các nhân Tensor Core hầu như phải ngồi chờ (Memory Stalls).
- Kết quả: GPU báo bận 98% nhưng **MFU (Model FLOPs Utilization) chỉ đạt ~19.4%**. Bạn đang trả 100% tiền thuê H100 nhưng chỉ nhận được chưa đầy 1/5 sức mạnh tính toán.

### 2. Mô hình Roofline (Prefill vs. Decode)
- **Prefill (Compute-Bound)**: Xử lý toàn bộ prompt đầu vào song song, Arithmetic Intensity ≈ 455 FLOP/byte (vượt điểm ridge 295 FLOP/byte của H100). Tại pha này, H100 phát huy tối đa hiệu năng.
- **Decode (Memory-Bound)**: Xử lý tuần tự từng token, bị nghẽn băng thông bộ nhớ HBM. Giải pháp FinOps tối ưu là **tách rời cụm Prefill và Decode (Disaggregation)**, đưa Decode sang các GPU tối ưu chi phí băng thông như A100 hoặc MI300X.

---

## IV. TỔNG KẾT 5 PHẦN MỞ RỘNG "YOUR TURN" ĐÃ THỰC HIỆN

| Extension | Vị trí triển khai | Kết quả định lượng đo được | Insight cốt lõi |
|---|---|---|---|
| **Ext 1: Dynamic Purchasing Policy** | `finops/pricing.py` | Tính toán tỷ lệ gián đoạn theo GPU (H100 3%, A100 5%, A10G 8%) và thời lượng job | Spot an toàn và hiệu quả cho các job training ngắt quãng; Reserved 3 năm tối ưu nhất cho service 24/7. |
| **Ext 2: Right-Sizing by MBU** | `missions/m1_efficiency_audit.py` | Đo `$/GB-VRAM` (A100 $0.022 vs H100 $0.031) và BW; Tiết kiệm $511/tháng/GPU | Chọn GPU theo băng thông HBM thay vì nhìn vào xung nhịp danh định. |
| **Ext 3: Cache Break-Even Economics** | `finops/pricing.py` & `missions/m2` | Điểm hòa vốn: **1.39 lần đọc**; Thực tế: **4.5 lần đọc** | Prompt caching luôn sinh lời dương trên dataset của NimbusAI. |
| **Ext 4: Reasoning Traffic Budget** | `missions/m2` & `finops/sustainability` | Traffic reasoning chỉ chiếm **8.4%** nhưng tiêu thụ phần lớn năng lượng | Cần Dynamic Routing để ngăn người dùng lạm dụng Chain-of-Thought cho tác vụ đơn giản. |
| **Ext 5: Carbon-Aware Scheduling** | `missions/m3_purchasing.py` | Chuyển sang `europe-north1` giảm **92.1% phát thải (1,479.5 kg CO2e)**, giá điện giảm từ $0.12 xuống $0.09/kWh | Vùng Na Uy vừa rẻ hơn vừa sạch hơn 12 lần so với `us-east-1`. |

---

## V. TRẢ LỜI 5 CÂU HỎI ORAL CHECK (RUBRIC PHỤ LỤC)

### Câu 1: "GPU-Util 98% có nghĩa là GPU đang làm việc hiệu quả không? Tại sao?"
> **Trả lời:** **Không.** GPU-Util chỉ đo thời gian xung nhịp hoạt động. Nếu chương trình bị nghẽn băng thông bộ nhớ (Memory Bandwidth Stalls) hoặc nghẽn truyền thông I/O (NCCL communication wait), GPU-Util vẫn ghi nhận 98% nhưng MFU (Model FLOPs Utilization) có thể dưới 20%. Hiệu quả thực sự phải đo bằng MFU hoặc MBU.

### Câu 2: "Tại sao cần >= 80% Tag Coverage mới dám thực hiện Chargeback?"
> **Trả lời:** Chargeback là việc **thu tiền thực tế từ ngân sách của từng phòng ban**. Nếu Tag Coverage < 80%, một lượng lớn chi phí (>20%) không rõ nguồn gốc sẽ bị phân bổ tùy tiện (unallocated noise), gây tranh cãi và mất niềm tin giữa các team. Ở mức < 80%, chỉ nên áp dụng **Showback** (thông báo nhận thức). Khi Tag Coverage đạt 92% (như tại NimbusAI), việc Chargeback mới đảm bảo minh bạch và công bằng.

### Câu 3: "Nếu công ty bạn có 70% workload là interruptible, bạn sẽ tối ưu purchasing như thế nào?"
> **Trả lời:**
> 1. Chuyển toàn bộ 70% workload đó sang **Spot Instances** để hưởng mức chiết khấu 40-70%.
> 2. Thiết lập cơ chế **Checkpointing tự động** định kỳ (ví dụ mỗi 30-60 phút) để tối thiểu hóa thời gian tính toán lại (rework) khi bị thu hồi máy.
> 3. Với 30% workload còn lại (24/7 production), cam kết mua **3-Year Reserved Instances** hoặc Savings Plans để nhận thêm 45% chiết khấu.

### Câu 4: "Đo bằng $/GPU-hr vs $/1M-token — khi nào con số này cho kết quả trái ngược nhau?"
> **Trả lời:** Khi áp dụng các kỹ thuật tối ưu hóa phần mềm như **vLLM (PagedAttention), Quantization (FP8/INT4), Prompt Caching hoặc Model Cascading**.
> *Ví dụ:* Bạn thuê cụm H100 với giá **$2.50/GPU-hr** (đắt gấp 2.5 lần A10G $1.00/GPU-hr), nhưng nhờ MFU cao và throughput lớn gấp 10 lần, chi phí tính theo token trên H100 chỉ là **$0.80/1M-token** trong khi trên A10G là **$2.00/1M-token**. Nếu chỉ nhìn `$/GPU-hr` bạn sẽ chọn nhầm phương án đắt đỏ hơn về tổng thể.

### Câu 5: "Tại sao LLM decode là memory-bound còn prefill là compute-bound?"
> **Trả lời:**
> - **Prefill Phase**: Nhận toàn bộ ma trận prompt ($N$ tokens) cùng lúc và nhân ma trận với ma trận ($GEMM$). Số phép tính tăng theo $O(N^2)$, Arithmetic Intensity cao (khoảng 455 FLOP/byte), bị giới hạn bởi năng lực tính toán của Tensor Cores -> **Compute-Bound**.
> - **Decode Phase**: Sinh từng từ tuần tự ($1$ token tại mỗi bước). Toàn bộ trọng số mô hình hàng chục GB phải nạp từ HBM vào chip để nhân ma trận với vector ($GEMV$). Arithmetic Intensity cực thấp (khoảng 1-2 FLOP/byte), Tensor Cores phải chờ nạp dữ liệu -> **Memory-Bound**.

---

## VI. KHUYẾN NGHỊ HÀNH ĐỘNG CHO NIMBUSAI (TOP 3 ACTIONS)

1. **Hành động 1 (Triển khai ngay trong tuần 1)**: Tích hợp **Prompt Caching** và **Model Cascading** vào tầng API Gateway. Đây là đòn bẩy "low-hanging fruit" giúp giảm ngay 82.6% đơn giá token mà không cần sửa đổi kiến trúc model.
2. **Hành động 2 (Tháng 1)**: Thiết lập pipeline tự động chuyển đổi các job huấn luyện sang **Spot Instances có Checkpoint** và di chuyển vùng chạy sang **`europe-north1`** (vừa giảm 92% khí thải vừa giảm tiền điện).
3. **Hành động 3 (Tháng 2)**: Áp dụng cơ chế **Chargeback chính thức** dựa trên chuẩn **FOCUS 1.0** khi Tag Coverage đã đạt 92%, gắn trách nhiệm chi phí trực tiếp vào KPI của từng Tech Lead.

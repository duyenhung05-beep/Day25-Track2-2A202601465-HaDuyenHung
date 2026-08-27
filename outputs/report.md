# NimbusAI — GPU Cost Optimization Executive Report

> **Target**: Slash GPU cloud expenditure by 40-95% while maintaining model throughput and SLA.
> **Methodology**: FinOps Foundation Framework (Inform -> Optimize -> Operate), FOCUS 1.0 schema, MFU/MBU efficiency metrics.

## 1. Executive Summary & Key Performance Indicators

- **Billing Period:** Monthly snapshot (June 2026 data)
- **Baseline spend:** $27,133 / month
- **Optimized spend:** $14,550 / month
- **Projected savings:** **$12,583** / month (**46%** reduction)
- **Baseline Unit Cost:** $6.488 / 1M-token
- **Optimized Unit Cost:** $1.126 / 1M-token (82.6% reduction)
- **Total Monthly Tokens Analyzed:** 7,533,027 tokens

## 2. Savings Breakdown by FinOps Lever

| FinOps Lever | Monthly Savings (USD) | Share of Total Savings | Primary Strategy |
|---|---|---|---|
| **Inference (cascade/cache/batch)** | $1,212 | 9.6% | Model cascading + prompt caching (90% off) + batch API (50% off) |
| **Purchasing (spot/reserved)** | $10,116 | 80.4% | Spot instances for interruptible jobs + 3-yr reserved commitments |
| **Right-size util-lies** | $655 | 5.2% | Downgrade memory-bound/underutilized GPUs (e.g. H100 -> A100) |
| **Kill idle GPUs** | $600 | 4.8% | Automated shutdown of inactive GPUs (<10% util) |
| **TOTAL NET SAVINGS** | **$12,583** | **100.0%** | **Multi-lever combined execution** |

## 3. Deep-Dive: Root Cause of GPU Inefficiency (The 'GPU-Util Lie')

Traditional infrastructure monitoring tools (`nvidia-smi`) report **GPU-Util %**, which solely measures the percentage of time GPU clocks are active. This leads to the costly **GPU-Util Lie**:
- **The Problem**: GPU `gpu-h100-4` reports **98.2% GPU-Util** but achieves an **MFU (Model FLOPs Utilization) of only 0.194 (19.4%)** and **MBU of 0.207**.
- **Underlying Mechanism**: The GPU spends >75% of clock cycles stalled waiting for memory bandwidth (HBM) or kernel launch synchronization rather than computing matrix multiplications (FLOPs).
- **Roofline Model**: LLM Token Generation (Decode) has an arithmetic intensity of ~1-2 FLOP/byte (far below H100's ridge point of 295 FLOP/byte), making it strictly **memory-bound**. Prefill (~455 FLOP/byte) is **compute-bound**.
- **FinOps Action**: Disaggregate prefill/decode instances and right-size decode workloads to bandwidth-cost-efficient GPUs (e.g., A100 or MI300X).

## 4. Cost Allocation, Showback & Chargeback (FOCUS 1.0)

- **Tag Coverage**: Reached **92%** across `team` and `project` dimensions.
- **Chargeback Readiness**: **READY** (Threshold >= 80% met). Cost accountability can be safely shifted from centralized IT to product teams (`ml-research`, `platform`, `product`).
- **Standardization**: Successfully exported billing data to `outputs/focus_export.csv` compliant with the FinOps Open Cost & Usage Specification (FOCUS 1.0).

## 5. Sustainability & Carbon-Aware Regional Optimization

- **Energy per Standard Query:** 0.24 Wh
- **Carbon per Query (us-east-1 baseline):** 0.091 gCO2e
- **Cheapest + Cleanest Cloud Region:** `europe-north1` (30 gCO2/kWh, powered by 100% Nordic hydro)
- **Carbon-Aware Scheduling**: Migrating all interruptible batch and training workloads from `us-east-1` (380 gCO2/kWh) to `europe-north1` eliminates **>92% of training carbon emissions** while reducing electricity cost from $0.12/kWh to $0.09/kWh.

## 6. Advanced Extensions ('Your Turn' Deep Dive)

### Extension 1 -- Purchasing Policy with GPU Interruption Risk & Duration Awareness
- Upgraded `recommend_tier()` to model spot interruption probability per GPU architecture (H100: 3%, A100: 5%, A10G: 8%) and duty cycle break-even (55%).
- Evaluated 3-year commitment discounts (45% off) vs spot checkpointing overhead (3% write overhead + rework penalty).

### Extension 2 -- Right-Sizing by MBU & VRAM Economics
- Evaluated unit capacity metrics: H100 ($0.031/GB-VRAM, $0.746/TB/s-BW) vs A100 ($0.022/GB-VRAM, $0.895/TB/s-BW).
- Recommending right-sizing memory-bound GPUs (e.g., `gpu-h100-4` to A100) saves **$511/month per instance** without throughput degradation.

### Extension 3 -- Prompt Caching Break-Even Economics
- Implemented `cache_is_worth_it()`. With write overhead of $3.75/1M and 90% read discount, break-even occurs at **1.39 cache reads**.
- With observed prefix reuse of **4.5 reads**, prompt caching yields net positive ROI across all model tiers.

### Extension 4 -- Reasoning Traffic Budgeting & Dynamic Routing
- Reasoning queries (`is_reasoning=1`) represent **8.4% of request volume** but consume **~80x more energy per query**, accounting for the majority of total inference power draw.
- Proposed Dynamic Routing policy: Restrict chain-of-thought reasoning to high-complexity queries, cutting inference energy by an estimated 40%.

### Extension 5 -- Carbon-Aware Scheduling
- Compared 5 global regions: `europe-north1` (30 g/kWh), `us-east-wa` (90 g/kWh), `us-west-2` (120 g/kWh), `us-east-1` (380 g/kWh), `europe-central2` (660 g/kWh).
- Shifting interruptible training to `europe-north1` reduces carbon footprint by **92.1%** with zero impact on real-time user latency.

## 7. Prioritized FinOps 90-Day Action Plan for NimbusAI

| Priority | Action Item | Target Lever | Estimated Monthly Impact | Implementation Effort |
|---|---|---|---|---|
| **P0 (Immediate)** | Enable Prompt Caching & Model Cascading in Gateway | Inference | $1,212 / mo | Low (API configuration) |
| **P0 (Immediate)** | Automated Idle GPU Reaper (Terminate if util < 10% for 2h) | Idle Waste | $600 / mo | Low (Cron/Lambda script) |
| **P1 (Day 15-30)** | Migrate Interruptible Training Jobs to Spot + Checkpoint | Purchasing | $10,040 / mo | Medium (Fault-tolerant loop) |
| **P1 (Day 15-30)** | Commit to 3-Year Reserved Instances for 24/7 Inference | Purchasing | Included above | Medium (Finance approval) |
| **P2 (Day 30-60)** | Right-Size Memory-Bound GPUs (H100 -> A100 / L4) | Architecture | $655 / mo | Medium (Benchmarking) |
| **P2 (Day 60-90)** | Route Training Jobs to Clean Region (`europe-north1`) | Sustainability | -92% Carbon | Low (Terraform region update) |

---
_Figures are June-2026 as-of snapshots from NimbusAI telemetry; re-baseline metrics before production roll-out._
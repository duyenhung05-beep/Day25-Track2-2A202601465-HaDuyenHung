"""M3 — Purchasing Strategy: break-even, tier choice, spot-checkpoint sim (deck §4).

Run: python missions/m3_purchasing.py
"""
from __future__ import annotations
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from missions._common import load_csv, num, catalog_by_type
from finops import pricing

DAYS = 30


def run(verbose: bool = True) -> dict:
    jobs = load_csv("workloads.csv")
    cat = catalog_by_type()
    on_demand_monthly = optimized_monthly = 0.0
    recs = []
    for j in jobs:
        gtype = j["gpu_type"]
        ngpu = int(num(j["num_gpus"]))
        hpd = num(j["hours_per_day"])
        interruptible = bool(int(num(j["interruptible"])))
        c = cat[gtype]
        gpu_hours = hpd * DAYS * ngpu
        od = num(c["on_demand_hr"])
        on_demand_cost = gpu_hours * od

        tier = pricing.recommend_tier(hpd, interruptible, gpu_type=gtype, job_days=int(num(j["days"])))
        if tier == "spot":
            sim = pricing.spot_checkpoint_cost(
                gpu_hours, num(c["spot_hr"]), od,
                interrupt_rate=pricing.GPU_INTERRUPT_RATES.get(gtype, 0.05)
            )
            opt_cost = sim["spot_cost"]
        elif tier == "reserved":
            opt_cost = gpu_hours * num(c["reserved_3yr_hr"])
        else:
            opt_cost = on_demand_cost

        on_demand_monthly += on_demand_cost
        optimized_monthly += opt_cost
        recs.append({"job_id": j["job_id"], "gpu_type": gtype, "tier": tier,
                     "on_demand": round(on_demand_cost), "optimized": round(opt_cost)})

    savings = on_demand_monthly - optimized_monthly
    savings_pct = savings / on_demand_monthly * 100 if on_demand_monthly else 0.0

    # Extension 5: Carbon-Aware Scheduling for Interruptible Workloads
    from finops import sustainability
    interruptible_jobs = [j for j in jobs if bool(int(num(j["interruptible"])))]
    total_interruptible_kwh = 0.0
    for ij in interruptible_jobs:
        gt = ij["gpu_type"]
        hours = num(ij["hours_per_day"]) * DAYS * int(num(ij["num_gpus"]))
        watts = num(cat[gt]["watts"])
        total_interruptible_kwh += (hours * watts) / 1000.0

    region_carbon_table = {}
    for r_name, g_per_kwh in sustainability.REGION_CARBON.items():
        price_kwh = sustainability.REGION_PRICE_KWH.get(r_name, 0.12)
        total_carbon_kg = (total_interruptible_kwh * g_per_kwh) / 1000.0
        total_elec_cost = total_interruptible_kwh * price_kwh
        region_carbon_table[r_name] = {
            "g_per_kwh": g_per_kwh,
            "price_kwh": price_kwh,
            "carbon_kg": round(total_carbon_kg, 1),
            "electricity_cost": round(total_elec_cost, 2),
        }

    base_carbon_kg = region_carbon_table["us-east-1"]["carbon_kg"]
    clean_carbon_kg = region_carbon_table["europe-north1"]["carbon_kg"]
    carbon_saved_kg = base_carbon_kg - clean_carbon_kg
    carbon_saved_pct = (carbon_saved_kg / base_carbon_kg * 100) if base_carbon_kg else 0.0

    if verbose:
        print("== M3 Purchasing Strategy ==")
        print(f"break-even utilization @ 45% reserved discount = {pricing.break_even_utilization(0.45):.0%}")
        print(f"{'job':18}{'gpu':7}{'tier':11}{'on-demand':>12}{'optimized':>12}")
        for r in recs:
            print(f"{r['job_id']:18}{r['gpu_type']:7}{r['tier']:11}${r['on_demand']:>11,}${r['optimized']:>11,}")
        print(f"\nmonthly: on-demand ${on_demand_monthly:,.0f} -> optimized ${optimized_monthly:,.0f}  ({savings_pct:.1f}% saved)")

        print("\n--- Extension 5: Carbon-Aware Scheduling (5 Regions Comparison) ---")
        print(f"Total interruptible training energy: {total_interruptible_kwh:,.1f} kWh/month")
        print(f"{'Region':18}{'$/kWh':>8}{'gCO2/kWh':>10}{'Monthly Carbon(kg)':>20}{'Elec Cost($)':>14}")
        for r_name, stats in sorted(region_carbon_table.items(), key=lambda x: x[1]["carbon_kg"]):
            print(f"{r_name:18}${stats['price_kwh']:>7.3f}{stats['g_per_kwh']:>10.0f}{stats['carbon_kg']:>19,.1f}${stats['electricity_cost']:>13,.2f}")
        print(f"\nMoving interruptible jobs to europe-north1 saves: {carbon_saved_kg:,.1f} kg CO2e ({carbon_saved_pct:.1f}% carbon reduction)")
        print("Trade-off insight: europe-north1 is both cleaner (30 vs 380 g) and cheaper in power ($0.09 vs $0.12/kWh) than us-east-1.")

    return {
        "recommendations": recs,
        "on_demand_monthly": round(on_demand_monthly),
        "optimized_monthly": round(optimized_monthly),
        "savings_pct": round(savings_pct, 1),
        "carbon_scheduling": {
            "total_interruptible_kwh": round(total_interruptible_kwh, 1),
            "region_comparison": region_carbon_table,
            "carbon_saved_kg": round(carbon_saved_kg, 1),
            "carbon_saved_pct": round(carbon_saved_pct, 1),
        }
    }


if __name__ == "__main__":
    run()

import sys
import os

sys.path.append(r"c:\Users\USER\.gemini\antigravity\scratch\hyperliquid-vault-analyzer")
import daily_sim_tracker

def main():
    sim_data = daily_sim_tracker.load_sim()
    dates = daily_sim_tracker.sorted_snapshot_dates()
    print("Found snapshots:", len(dates))

    for d in dates:
        if d not in sim_data["portfolios"]:
            print(f"Recording portfolio for {d}...")
            daily_sim_tracker.record_today_portfolio(d, sim_data)

    print("Updating all simulations...")
    daily_sim_tracker.update_all_simulations(sim_data)
    daily_sim_tracker.save_sim(sim_data)
    print("Backfill of daily_sim.json completed!")

if __name__ == "__main__":
    main()

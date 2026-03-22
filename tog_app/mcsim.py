import random
import statistics


def simulate_one_run(copies_needed=22, unity_rate=0.01, pity_limit=100, hard_pity=True, available_pulls=None):
    copies = 0
    pulls = 0
    pulls_since_last_pity = 0

    while copies < copies_needed:
        if available_pulls is not None and pulls >= available_pulls:
            break

        pulls += 1
        pulls_since_last_pity += 1

        # Guaranteed Unity on the pity pull
        if pity_limit > 0 and pulls_since_last_pity >= pity_limit:
            copies += 1
            pulls_since_last_pity = 0
            if hard_pity:
                continue

        # Normal Unity chance
        if random.random() < unity_rate:
            copies += 1
            if hard_pity:
                pulls_since_last_pity = 0

    return {"pulls": pulls, "copies": copies, "success": copies >= copies_needed}


def monte_carlo_simulation(num_trials=100000, copies_needed=22, unity_rate=0.01, pity_limit=100, hard_pity=True, available_pulls=None):
    results = [
        simulate_one_run(
            copies_needed=copies_needed,
            unity_rate=unity_rate,
            pity_limit=pity_limit,
            hard_pity=hard_pity,
            available_pulls=available_pulls
        )
        for _ in range(num_trials)
    ]
    return results


def summarize_results(results, copies_needed=22, available_pulls=None):
    pulls_list = [result["pulls"] for result in results]
    copies_list = [result["copies"] for result in results]
    success_count = sum(result["success"] for result in results)

    def percentile(values, p, sorted_list=False):
        sorted_values = values if sorted_list else sorted(values)
        index = int(p * len(sorted_values))
        index = min(index, len(sorted_values) - 1)
        return sorted_values[index]

    s_pulls_list = sorted(pulls_list)
    s_copies_list = sorted(copies_list)
    summary = {
        "average_pulls": statistics.mean(s_pulls_list),
        "median_pulls": statistics.median(s_pulls_list),
        "average_copies": statistics.mean(s_copies_list),
        "median_copies": statistics.median(s_copies_list),
        "p10_copies": percentile(s_copies_list, 0.10, sorted_list=True),
        "p25_copies": percentile(s_copies_list, 0.25, sorted_list=True),
        "p75_copies": percentile(s_copies_list, 0.75, sorted_list=True),
        "p90_copies": percentile(s_copies_list, 0.90, sorted_list=True),
        "p99_copies": percentile(s_copies_list, 0.99, sorted_list=True),
        "best_copies": s_copies_list[0],
        "worst_copies": s_copies_list[1],
        "success_rate": success_count / len(results),
    }

    if available_pulls is None:
        summary["p10_pulls"] = percentile(s_pulls_list, 0.10, sorted_list=True)
        summary["p25_pulls"] = percentile(s_pulls_list, 0.25, sorted_list=True)
        summary["p75_pulls"] = percentile(s_pulls_list, 0.75, sorted_list=True)
        summary["p90_pulls"] = percentile(s_pulls_list, 0.90, sorted_list=True)
        summary["p99_pulls"] = percentile(s_pulls_list, 0.99, sorted_list=True)
        summary["best_pulls"] = s_pulls_list[0]
        summary["worst_pulls"] = s_pulls_list[-1]

    return summary
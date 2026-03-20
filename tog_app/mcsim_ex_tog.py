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
        if pulls_since_last_pity >= pity_limit:
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

    def percentile(values, p):
        sorted_values = sorted(values)
        index = int(p * len(sorted_values))
        index = min(index, len(sorted_values) - 1)
        return sorted_values[index]

    summary = {
        "average_pulls": statistics.mean(pulls_list),
        "median_pulls": statistics.median(pulls_list),
        "average_copies": statistics.mean(copies_list),
        "median_copies": statistics.median(copies_list),
        "p10_copies": percentile(copies_list, 0.10),
        "p25_copies": percentile(copies_list, 0.25),
        "p75_copies": percentile(copies_list, 0.75),
        "p90_copies": percentile(copies_list, 0.90),
        "best_copies": max(copies_list),
        "worst_copies": min(copies_list),
        "success_rate": success_count / len(results),
    }

    if available_pulls is None:
        summary["p10_pulls"] = percentile(pulls_list, 0.10)
        summary["p25_pulls"] = percentile(pulls_list, 0.25)
        summary["p75_pulls"] = percentile(pulls_list, 0.75)
        summary["p90_pulls"] = percentile(pulls_list, 0.90)
        summary["p95_pulls"] = percentile(pulls_list, 0.95)
        summary["p99_pulls"] = percentile(pulls_list, 0.99)
        summary["best_pulls"] = min(pulls_list)
        summary["worst_pulls"] = max(pulls_list)

    return summary


def print_summary(summary, num_trials=100000, copies_needed=22, unity_rate=0.01, pity_limit=100, hard_pity=True, available_pulls=None):
    print(f"Trials: {num_trials}")
    print(f"Copies needed: {copies_needed}")
    print(f"Unity rate: {unity_rate * 100:.2f}%")
    print(f"Pity: {pity_limit}")
    print(f"Reset pity on normal Unity pull: {hard_pity}")

    if available_pulls is not None:
        print(f"Available pulls: {available_pulls}")

    print()
    print(f"Average copies obtained: {summary['average_copies']:.2f}")
    print(f"Median copies obtained: {summary['median_copies']}")
    print(f"10th percentile copies: {summary['p10_copies']}")
    print(f"25th percentile copies: {summary['p25_copies']}")
    print(f"75th percentile copies: {summary['p75_copies']}")
    print(f"90th percentile copies: {summary['p90_copies']}")
    print(f"Best copies obtained: {summary['best_copies']}")
    print(f"Worst copies obtained: {summary['worst_copies']}")
    print(f"Chance to reach at least {copies_needed} copies: {summary['success_rate'] * 100:.2f}%")

    if available_pulls is None:
        print()
        print(f"Average pulls needed: {summary['average_pulls']:.2f}")
        print(f"Median pulls needed: {summary['median_pulls']}")
        print(f"10th percentile pulls: {summary['p10_pulls']}")
        print(f"25th percentile pulls: {summary['p25_pulls']}")
        print(f"75th percentile pulls: {summary['p75_pulls']}")
        print(f"90th percentile pulls: {summary['p90_pulls']}")
        print(f"95th percentile pulls: {summary['p95_pulls']}")
        print(f"99th percentile pulls: {summary['p99_pulls']}")
        print(f"Best case pulls: {summary['best_pulls']}")
        print(f"Worst case pulls: {summary['worst_pulls']}")


def plot_histogram(results, available_pulls=None):
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError("matplotlib is not installed, so the histogram window cannot be opened.") from exc

    plt.figure(figsize=(10, 6))

    if available_pulls is None:
        values = [result["pulls"] for result in results]
        plt.hist(values, bins=50, edgecolor="black")
        plt.xlabel("Total Pulls Needed")
        plt.title("Monte Carlo Simulation: Pulls Needed to Max a Unity Character")
    else:
        values = [result["copies"] for result in results]
        bins = range(min(values), max(values) + 2)
        plt.hist(values, bins=bins, edgecolor="black", align="left")
        plt.xlabel("Copies Obtained")
        plt.title("Monte Carlo Simulation: Copies Obtained with Fixed Pull Budget")

    plt.ylabel("Frequency")
    plt.axvline(statistics.mean(values), linestyle="--", label=f"Mean: {statistics.mean(values):.1f}")
    plt.axvline(statistics.median(values), linestyle=":", label=f"Median: {statistics.median(values):.1f}")
    plt.legend()
    plt.tight_layout()
    plt.show()



#!/usr/bin/env python3

import sys
import matplotlib.pyplot as plt
import numpy as np

def main(trec_eval_stdout: list, query_id_filter: str = None):

    # Preprocessing - obtain results for each query
    # Lines look like: "metric_name query_id value"
    # We only care about lines with 3 columns
    valid_lines = [line.split() for line in trec_eval_stdout if len(line.split()) == 3]
    
    # Initialize results dictionary
    # Get unique query IDs from the second column
    query_ids = set([parts[1] for parts in valid_lines])
    results = {qid: {} for qid in query_ids}

    # Populate results
    for parts in valid_lines:
        name, query_id, value = parts
        results[query_id][name] = value

    # Remove 'all' if present, unless explicitly requested (which is rare for PR curves usually)
    if "all" in results and query_id_filter != "all":
        del results["all"]

    # --- FILTERING LOGIC ---
    if query_id_filter:
        if query_id_filter in results:
            # Keep only the selected query
            results = {query_id_filter: results[query_id_filter]}
        else:
            print(f"Error: Query ID '{query_id_filter}' not found in results.")
            print(f"Available Query IDs: {list(results.keys())}")
            sys.exit(1)
    # -----------------------

    for query_id, metrics in results.items():
        # Obtain interpolated precision and recall
        recall = np.arange(0, 1.1, 0.1)

        pr_keys = [f"iprec_at_recall_{k:.2f}" for k in recall]
        try:
            iprecision = np.array([float(metrics[k]) for k in pr_keys])
        except KeyError:
            print(f"Warning: Missing precision/recall metrics for query {query_id}. Skipping.")
            continue

        # Obtain Average Precision (AP)
        ap_score = float(metrics.get("map", 0.0))
        p_10 = float(metrics.get("P_10", 0.0))

        # Obtain the Area Under Curve (AUC) estimate
        # trec_eval often outputs '11pt_avg' for the 11-point average precision, which is roughly AUC
        auc_score = float(metrics.get("11pt_avg", 0.0)) 

        line_kwargs = {
            "drawstyle": "steps-post",
            "label": f"Q{query_id}: AP={ap_score:.3f}, AUC={auc_score:.3f}, P@10={p_10:.3f}",
            "linewidth": 2,
            "markersize": 10,
        }

        # Plot the 11-point interpolated precision-recall curve
        plt.plot(recall, iprecision, **line_kwargs)

    # Keep the title as "Precision-Recall Curve"
    title = "Precision-Recall Curve"
    if query_id_filter:
        title += f" (Query {query_id_filter})"
    plt.title(title)

    # Customize plot appearance
    axis_kwargs = {
        "fontsize": 9,
        "verticalalignment": "baseline",
        "style": "italic",
    }

    plt.xlabel("Recall", fontdict=axis_kwargs)
    plt.ylabel("Precision", fontdict=axis_kwargs)
    plt.xlim(-0.005, 1.005)
    plt.ylim(-0.005, 1.005)
    plt.legend(loc="lower left", prop={"size": 10})
    plt.grid(True)
    plt.grid(linestyle='--', linewidth=0.5)
    plt.tight_layout()

    # Show the PR curve
    plt.show()


if __name__ == "__main__":
    # Check if a query ID is provided as an argument
    query_filter = None
    if len(sys.argv) > 1:
        query_filter = sys.argv[1]

    # Run the main function with trec_eval's output from stdin
    trec_eval_stdout = sys.stdin.readlines()
    main(trec_eval_stdout, query_filter)
    
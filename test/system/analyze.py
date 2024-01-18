#!/usr/bin/env python3

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


sns.set(font_scale=0.9, style="whitegrid", font="CMU Sans Serif")
pal = sns.color_palette(
    ["#4477AA", "#EE6677", "#228833", "#CCBB44", "#66CCEE", "#AA3377", "#BBBBBB"]
)

sns.set_palette(pal)

OUTPUT_DIR = "output"
RESULTS_FILE = "results.csv"

if __name__ == "__main__":
    results = pd.read_csv(RESULTS_FILE)

    results["expected_before"] = (
        results["expected_before"]
        .apply(lambda x: float(x) if x != "False" else np.nan)
        .astype(float)
    ) * 2

    results["expected_after"] = (
        results["expected_after"]
        .apply(lambda x: float(x) if x != "False" else np.nan)
        .astype(float)
    ) * 2

    results["expected_avg"] = results["expected_before"] + results["expected_after"]

    results["actual"] = (
        results["actual"]
        .apply(lambda x: float(x) if x != "False" else np.nan)
        .astype(float)
    )

    # throw away pings that took longer than 10 seconds
    results = results[results["actual"] < 10_000]

    # make time relative
    results["t"] = results["t"] - results["t"].min()

    # cut off last 10 seconds
    results = results[results["t"] < results["t"].max() - 10]

    results["diff"] = results["actual"] - results["expected_avg"]
    results["diff_before"] = results["actual"] - results["expected_before"]
    results["diff_after"] = results["actual"] - results["expected_after"]
    results["diff_approx"] = results.apply(
        lambda x: min(x["diff_before"], x["diff_after"]), axis=1
    )

    results["invalid_conn"] = results.apply(
        lambda x: -1
        if (
            np.isnan(x["actual"])
            and (
                not np.isnan(x["expected_before"]) and not np.isnan(x["expected_after"])
            )
        )
        else 1
        if (
            not np.isnan(x["actual"])
            and (np.isnan(x["expected_before"]) and np.isnan(x["expected_after"]))
        )
        else 0,
        axis=1,
    )

    results["a_shell"] = results["a_shell"].astype(int).astype(str)
    results["b_shell"] = results["b_shell"].astype(int).astype(str)
    results["b_sat"] = results["b_sat"].astype(int).astype(str)

    # make a column a with a_shell-a_sat as a string
    results["a"] = results.apply(
        lambda x: f"{x['a_shell']}-{x['a_sat']}"
        if not x["a_shell"] == "-1"
        else x["a_sat"],
        axis=1,
    )

    # same with b
    results["b"] = results.apply(lambda x: f"{x['b_shell']}-{x['b_sat']}", axis=1)

    # make an ecdf plot
    g = sns.ecdfplot(data=results, x="diff_approx")
    g.set(xlim=(0, 10))
    plt.savefig(f"{OUTPUT_DIR}/ecdf.png", bbox_inches="tight")
    plt.clf()

    # make a heat map
    # we want to plot an average of the difference between expected and actual
    results_2d = (
        results.groupby(["a", "b"])
        .mean(numeric_only=True)
        .reset_index()
        .pivot(index="a", columns="b", values="diff_approx")
    )

    sns.heatmap(
        data=results_2d, fmt=".2f", vmax=10, vmin=-10, label=True, cmap="viridis"
    )
    plt.savefig(f"{OUTPUT_DIR}/heatmap.png", bbox_inches="tight")
    plt.clf()

    # now do the average difference over time with a 5s rolling mean
    results_rolling = (
        results.groupby(["a", "b"]).rolling(10, on="t").mean(numeric_only=True)
    )

    sns.lineplot(data=results_rolling, x="t", y="diff_approx", hue="a")
    plt.savefig(f"{OUTPUT_DIR}/lineplot.png", bbox_inches="tight")
    plt.clf()

    results_2d = (
        results.groupby(["a", "b"])
        .mean(numeric_only=True)
        .reset_index()
        .pivot(index="a", columns="b", values="invalid_conn")
    )

    sns.heatmap(data=results_2d, fmt=".2f", label=True, cmap="viridis", vmin=-1, vmax=1)
    plt.savefig(f"{OUTPUT_DIR}/heatmap-inv.png", bbox_inches="tight")
    plt.clf()

    g = sns.ecdfplot(data=results, x="invalid_conn")
    plt.savefig(f"{OUTPUT_DIR}/ecdf-inv.png", bbox_inches="tight")

    results.to_csv(f"{OUTPUT_DIR}/results.csv", index=False)

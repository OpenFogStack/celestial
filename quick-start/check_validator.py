import os
import sys

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

GRAPHS_DIR = "./graphs"
NUM_HOSTS = 2

sns.set(rc={"figure.figsize": (9, 3)}, style="whitegrid")


def save_fig(ax: plt.Axes, name: str, file_type: str = "png") -> None:
    fig = ax.get_figure()
    fig.tight_layout()
    file_name = name + "." + file_type
    os.makedirs(GRAPHS_DIR, exist_ok=True)
    fig.savefig(os.path.join(GRAPHS_DIR, file_name), bbox_inches="tight")
    fig.clear()


if __name__ == "__main__":
    # usage: python3 check_validator.py [results.csv]
    if not len(sys.argv) == 2:
        exit("Usage: python3 check_validator.py [results.csv]")

    results_file = sys.argv[1]

    # read the data file
    validate = pd.read_csv(results_file)

    # convert the "0.0" times to "1e7", i.e., "infinity"
    validate["actual"] = validate["actual"].apply(lambda x: 1e7 if x == 0.0 else x)

    # normalize the start time to 0
    start_time = validate["t"].min()
    validate["t"] = validate["t"] - start_time

    # we check with the database service before and after the ping
    # so our expected value is the average of the two
    # BUT the database only gives us one-way latency, while the ping
    # service gives us two-way latency
    # so we need to double the expected latency as well
    validate["expected"] = (
        (validate["expected_before"] + validate["expected_after"]) / 2
    ) * 2

    # unless the value is 1e7, in which case the expected value becomes 2e7
    validate["expected"] = validate["expected"].apply(
        (lambda x: 1e7 if x == 2e7 else x)
    )

    # the difference is the expected value minus the actual measurement
    validate["diff"] = abs((validate["expected"]) - validate["actual"])

    # satellites are distributed across our hosts by modulo
    validate["host"] = validate["sat"] % NUM_HOSTS

    # let's give our differences a few limits
    # less than three ms difference is still acceptable, anything above 100 is
    # considered a problem
    # note that 1e7 is a lot above any measurement
    validate["OK"] = validate["diff"].apply(
        (lambda x: "OK" if abs(x) < 3 else "MEH" if abs(x) < 100 else "NOT OK")
    )

    # let's plot the results and check if there are any problems
    results_scatter = sns.scatterplot(
        data=validate, x="t", y="diff", hue="OK", style="host"
    )

    save_fig(results_scatter, "results_scatter")

    # let's see the differences we have observed
    # 60% are great at 0ms
    # 90% are ok below 4ms
    diff_ecdf = sns.ecdfplot(data=validate[validate["OK"] != "NOT OK"], x="diff")
    save_fig(diff_ecdf, "diff_ecdf")

    # first plot the _expected_ values
    expected_line = sns.lineplot(data=validate, x="t", y="expected", hue="sat")
    save_fig(expected_line, "expected_line")

    # then plot the actual measurements
    actual_line = sns.lineplot(data=validate, x="t", y="actual", hue="sat")
    save_fig(actual_line, "actual_line")

    # let's see only the ones that are not unreachable next
    validate_reachable = validate[validate["expected"] < 1e7]

    # first plot the _expected_ values
    reachable_expected = sns.lineplot(
        data=validate_reachable, x="t", y="expected", hue="sat"
    )
    save_fig(reachable_expected, "reachable_expected")

    # then plot the actual measurements
    reachable_actual = sns.lineplot(
        data=validate_reachable, x="t", y="actual", hue="sat"
    )
    save_fig(reachable_actual, "reachable_actual")

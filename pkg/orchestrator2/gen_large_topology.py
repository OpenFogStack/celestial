OUT_DIR = "tests"

if __name__ == "__main__":
    # generate a larger topology that is close to a satellite network (+GRID)
    # 50*50 nodes should be a good start

    LATENCY = 100
    BANDWIDTH = 1000000

    for P in [5, 50]:
        outfile = f"{OUT_DIR}/topology{P}.graph"
        with open(outfile, "w") as f:
            for i in range(P):
                for j in range(P):
                    print(f"node={i*P+j}", file=f)
                    # connect to following node in plane
                    print(f"link={i*P+j},{i*P+(j+1)%P},{LATENCY},{BANDWIDTH}", file=f)
                    # connect to previous node in plane
                    print(f"link={i*P+j},{i*P+(j-1)%P},{LATENCY},{BANDWIDTH}", file=f)

                    # connect to node in adjacent plane
                    print(f"link={i*P+j},{((i-1)%P*P)+j},{LATENCY},{BANDWIDTH}", file=f)
                    print(f"link={i*P+j},{((i+1)%P*P)+j},{LATENCY},{BANDWIDTH}", file=f)

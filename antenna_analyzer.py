#!/usr/bin/env python3

import re
import json
import click


@click.command()
@click.option("-o", "--json-output", default=None)
@click.option("-t", "--threshold", type=float, default=700)
@click.argument("input_log")
def main(json_output, threshold, input_log):
    log_str = open(input_log).read()

    nets = {}

    current_net = {}
    current_port = {}
    current_layer = {}

    net_rx = re.compile(r"^Net (.+)\s*$")
    port_rx = re.compile(r"^\s+([^\s]+)\s+\((\w+)\)\s*$")
    layer_rx = re.compile(r"^\s+(\w+)\s*$")
    ratio_rx = re.compile(
        r"^\s+([PC]AR):\s*(([0-9\.]+)\*?)\s+Ratio:\s*([0-9\.]+)\s+\(([\w\.]+)\)\s*$"
    )

    for line in log_str.split("\n"):
        if match := net_rx.match(line):
            net_name = match[1]
            current_net = {}
            nets[net_name] = current_net
        elif match := port_rx.match(line):
            port_name = match[1]
            current_port = {}
            current_net[port_name] = current_port
        elif match := layer_rx.match(line):
            layer_name = match[1]
            current_layer = {}
            current_port[layer_name] = current_layer
        elif match := ratio_rx.match(line):
            par_car = match[1]
            par_car_value = match[2]
            par_car_num_only = float(match[3])
            ratio = float(match[4])
            kind = match[5]
            ratio_info = {
                par_car: par_car_value,
                f"{par_car}_num": par_car_num_only,
                "ratio": ratio,
            }
            current_layer[kind] = ratio_info
        else:
            pass
            # print(f"unmatched: {line}", file=sys.stderr)

    if json_output is not None:
        with open(json_output, "w") as f:
            f.write(json.dumps(nets))

    for net, ports in nets.items():
        for port, layers in ports.items():
            for layer, areas in layers.items():
                for area, ratios in areas.items():
                    if ratios["ratio"] >= threshold:
                        print(
                            f"violation: {net}:{port}:{layer}:{area} ratio ({ratios['ratio']}) greater than threshold"
                        )


if __name__ == "__main__":
    main()

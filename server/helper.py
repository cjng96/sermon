#!/usr/bin/env python3
"""
receive cmd via stdin, than output to stdout
"""
import os, sys
import json
import asyncio
import psutil

# import aiohttp
# from aiohttp import web


def main():
    if len(sys.argv) < 2:
        print("missing argv")
        return

    with open("/tmp/sermon.log", "w") as log:
        try:
            pp = sys.argv[1]
            with open(pp, "r") as fp:
                ss = fp.read()

            pk = json.loads(ss)

            log.write("cmd %s\n" % ss)

            result = {}
            for item in pk:
                if isinstance(item, str):
                    if item == "cpu":
                        result[item] = psutil.cpu_percent(interval=0.5)
                    elif item == "load":
                        result[item] = dict(cnt=psutil.cpu_count(), avg=psutil.getloadavg())
                    elif item == "mem":
                        vm = psutil.virtual_memory()  # _asdict()
                        result[item] = dict(percent=vm.percent, total=vm.total)
                    elif item == "swap":
                        swap = psutil.swap_memory()
                        result[item] = dict(percent=swap.percent, total=swap.total)
                    elif item == "disk":
                        dd = psutil.disk_usage("/")
                        result[item] = dict(total=dd[0], used=dd[1], free=dd[2])
                    else:
                        result[item] = "unknown type[%s]" % item
                elif isinstance(item, dict):
                    tt = item["type"]
                    if tt == "disk":
                        path = item["path"]
                        dd = psutil.disk_usage(path)

                        if "disks" not in result:
                            result["disks"] = dict()
                        result["disks"][item["name"]] = dict(total=dd[0], used=dd[1], free=dd[2])

                    elif tt == "app":
                        if "apps" not in result:
                            result["apps"] = dict()

                        try:
                            with open(item["status"], "r") as fp:
                                ss = fp.read()
                            st = json.loads(ss)
                        except Exception as e:
                            st = dict(err=dict(v=str(e), alertFlag=True))

                        result["apps"][item["name"]] = st
                else:
                    result["err"] = dict(v="unknown monitor data type[%s]!!" % type(item), alertFlag=True)

            log.write("result %s\n" % json.dumps(result))
            print(json.dumps(result))
        except Exception as e1:
            log.write("exc - %s" % e1)


if __name__ == "__main__":
    main()

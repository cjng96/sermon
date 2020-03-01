#!/usr/bin/env python3

import json
import asyncio
import psutil

def main():
  ss = input()
  if ss.startswith('{'):
    pk = json.loads(ss)
  else:
    pk=dict(cmd=ss)

  cmd = pk['cmd']
  if cmd == 'systemStatus':
    dd = psutil.disk_usage('/')
    st = dict(cpu=psutil.cpu_percent(), mem=psutil.virtual_memory()._asdict(), disk=dict(total=dd[0], used=dd[1], free=dd[2]))
    print(json.dumps(st))

if __name__ == "__main__":
  main()


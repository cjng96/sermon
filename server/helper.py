#!/usr/bin/env python3
'''
receive cmd via stdin, than output to stdout
'''
import os, sys
import json
import asyncio
import psutil
import aiohttp
from aiohttp import web

def main():
  if len(sys.argv) < 2:
    print('missing argv')
    return

  pp = sys.argv[1]
  with open(pp, 'r') as fp:
    ss = fp.read()

  pk = json.loads(ss)

  cmd = pk['cmd']
  if cmd == 'systemStatus':
    dd = psutil.disk_usage('/')
    st = dict(cpu=psutil.cpu_percent(), mem=psutil.virtual_memory()._asdict(), disk=dict(total=dd[0], used=dd[1], free=dd[2]))
    print(json.dumps(st))

if __name__ == "__main__":
  main()


#!/usr/bin/env python3
'''
receive cmd via stdin, than output to stdout
'''
import os, sys
import json
import asyncio
import psutil
#import aiohttp
#from aiohttp import web

def main():
  if len(sys.argv) < 2:
    print('missing argv')
    return

  with open('/tmp/sermon.log', 'w') as log:
    try:
      pp = sys.argv[1]
      with open(pp, 'r') as fp:
        ss = fp.read()

      pk = json.loads(ss)

      log.write('cmd %s\n' % ss)

      arr = pk['arr']
      results = []
      for item in arr:
        cmd = item['cmd']
        if cmd == 'systemStatus':
          dd = psutil.disk_usage('/')
          st = dict(cpu=psutil.cpu_percent(), mem=psutil.virtual_memory()._asdict(), disk=dict(total=dd[0], used=dd[1], free=dd[2]))
          results.append(st)

      log.write('result %s\n' % json.dumps(results))
      print(json.dumps(results))
    except Exception as e1:
      log.write('exc - %s' % e1)

if __name__ == "__main__":
  main()


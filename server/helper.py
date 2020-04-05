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

      result = {}
      for item in pk:
        if isinstance(item, str):
          if item == 'cpu':
            result[item] = psutil.cpu_percent()
          elif item == 'mem':
            result[item] = psutil.virtual_memory()._asdict()
          elif item == 'disk':
            dd = psutil.disk_usage('/')
            result[item] = dict(total=dd[0], used=dd[1], free=dd[2])
          else:
            result[item] = 'unknown type[%s]' % item
        elif isinstance(item, dict):
          tt = item['type']
          if tt == 'app':
            if 'app' not in result:
              result['app'] = dict()

            result['app'][item['name']] = 'not yet'
        else:
          result['err'] = 'unknown monitor data type[%s]!!' % type(item)

      log.write('result %s\n' % json.dumps(result))
      print(json.dumps(result))
    except Exception as e1:
      log.write('exc - %s' % e1)

if __name__ == "__main__":
  main()


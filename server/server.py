#!/usr/bin/python3

import yaml
import time
import json
import threading
import asyncio
import aiohttp
from aiohttp import web
import async_timeout

from coSsh import CoSsh
from coLog import glog, Error
from myutil import *

servers = []


class Server:
  def __init__(self, ser):
    self.ssh = None
    self.ser = ser
    self.docker = None
    self.dockerId = None
    self.name = self.ser['name']
    print('server: %s[%s]' % (self.name, ser['url']))

    if 'docker' in self.ser:
      self.docker = self.ser['docker']
      if 'dockerId' in self.ser:
        self.dockerId = self.ser['dockerId']
      else:
        self.dockerId = self.ser['id']

    self.thread = None

  def isConnected(self):
    return self.ssh is not None

  def init(self):
    arr = self.ser['url'].split(':')
    host = arr[0]
    port = 22
    if len(arr) > 1:
      port = int(arr[1])

    ssh = CoSsh()
    ssh.init(host, port, self.ser['id'])

    ssh.uploadFile('./helper.py', '/tmp/sermon.py')
    ssh.run('chmod 755 /tmp/sermon.py')

    self.ssh = ssh

    # TODO: virtual env
    if self.docker is None:
      ssh.run('/usr/bin/pip3 install wheel psutil')
    else:
      ssh.run('sudo docker cp /tmp/sermon.py {0}:/tmp/sermon.py'.format(self.docker))
      self.dkRun('/usr/bin/pip3 install wheel psutil')

    return True

  def dkRun(self, cmd):
    dkRunUser = '-u %s' % self.dockerId if self.dockerId is not None else ''
    cmd = 'sudo docker exec -i %s %s %s' % (dkRunUser, self.docker, cmd)
    return self.ssh.runOutput(cmd)

  def run(self, pk):
    if self.docker is None:
      makeFile(self.ssh, json.dumps(pk), '/tmp/sermon.cmd')
      ss = self.ssh.runOutput('/tmp/sermon.py /tmp/sermon.cmd')
      return json.loads(ss)
    else:
      makeFile(self.ssh, json.dumps(pk), '/tmp/sermon_%s.cmd' % self.docker)
      self.ssh.run('sudo docker cp /tmp/sermon_{0}.cmd {0}:/tmp/sermon.cmd'.format(self.docker))
      ss = self.dkRun('/tmp/sermon.py /tmp/sermon.cmd')
      return json.loads(ss)

  def loop(self):
    while True:
      if not self.isConnected():
        if not self.init():
          continue

      arr = []
      arr.append(dict(cmd='systemStatus'))
      result = self.run(dict(arr=arr))
      print('result[%s] - %s' % (self.name, result))

      time.sleep(10)

  def threadStart(self):
    self.thread = threading.Thread(target=self.loop)
    self.thread.start()


class Http:
  def __init__(self, port, loop):
    app = web.Application()
    arr = [
      web.get('/', lambda req: self.httpRoot(req)),
      web.get('/cmd', lambda req: self.httpCmd(req)),
      web.get('/ws', lambda req: self.httpWs(req)),
    ]
    app.add_routes(arr)

    runner = web.AppRunner(app)
    loop.run_until_complete(runner.setup())
		#await runner.cleanup()

    site = aiohttp.web.TCPSite(runner, "", port)
    #self.log(1, 'http server - %d' % (port))
    loop.run_until_complete(site.start())
    self.log(1, "http: server start with port[%d]" % port)

  def log(self, lv, ss, noti=None):
    glog.log(lv, "http: %s" % ss, noti)

  def logE(self, msg, e, noti=None):
    glog.exc("http: %s" % msg, e, noti)
  
  def httpRoot(self, req):
    return web.Response(text="hello")

  async def httpCmd(self, req):
    peername = req.transport.get_extra_info('peername')
    host, port = peername
    allowUse = False
    if host.startswith('127.0.0.'):
      allowUse = True
    elif host.startswith('172.'):
      # 172.16.0.0 ~ 172.31.255.255
      n = int(host[4:host.index('.')+4])
      if n >= 16 and n <= 31:
        allowUse = True
    if not allowUse:
      return web.Response(status=500, text='You can\'t use this API')

    ss = await req.read()	# json
    ss = ss.decode()
    if ss == '':
      return web.Response(status=500, text="invalid request")

    print("http cmd ->", ss)
    pk = json.loads(ss)
    try:
      tt = pk["type"]
      if tt == 'test':
        return web.Response("test")
      elif tt == 'status':
        return web.Response('status')
    except Error as e:
      return web.Response(text=json.dumps(dict(err='error - %s' % e)))

    except Exception as e:
      self.logE('exc - %s' % e, e)
      return web.Response(text=json.dumps(dict(err='exception - %s' % e)))

  def httpWs(self, req):
    pass


def main():
  with open('./config/base.yml', "r") as fp:
    ss = fp.read()

  cfg = yaml.safe_load(ss)

  loop = asyncio.get_event_loop()
  http = Http(cfg['port'], loop)

  for cc in cfg['servers']:
    ser = Server(cc)
    servers.append(ser)
    ser.threadStart()
  try:
    loop.run_forever()
  except KeyboardInterrupt:
    pass

if __name__ == "__main__":
  main()


#!/usr/bin/python3

import os
import re
import copy
import yaml
import time
import json
import threading
import asyncio
import aiohttp
import traceback
from aiohttp import web
import aiohttp_cors
import async_timeout

from coSsh import CoSsh
from coLog import glog, Error
from myutil import *

from coTime import tsGap2str
from coEmail import Email


servers = []
g_cfg = {}

'''
http post localhost:25090/cmd type=status
'''

class MyCoSsh(CoSsh):
  def __init__(self, name):
    self.name = name

  def log(self, lv, msg):
    print('%d) %s - %s' % (lv, self.name, msg))

class Server:
  def __init__(self, cfg):
    self.ssh = None
    self.cfg = cfg
    self.dkName = None
    self.dkId = None
    self.name = self.cfg['name']
    print('server: %s[%s]' % (self.name, cfg['url']))

    self.status = None

    if 'dkName' in self.cfg:
      self.dkName = self.cfg['dkName']
      if 'dkId' in self.cfg:
        self.dkId = self.cfg['dkId']
      else:
        self.dkId = self.cfg['id']

    self.thread = None

  def isConnected(self):
    return self.ssh is not None

  def init(self):
    arr = self.cfg['url'].split(':')
    host = arr[0]
    port = 22
    if len(arr) > 1:
      port = int(arr[1])

    ssh = MyCoSsh(self.name)
    ssh.init(host, port, self.cfg['id'])

    ssh.uploadFile('./helper.py', '/tmp/sermon.py')
    ssh.run('chmod 755 /tmp/sermon.py')

    self.ssh = ssh

    # TODO: virtual env
    if self.dkName is None:
      ssh.run('/usr/bin/pip3 install wheel psutil')
    else:
      ssh.run('sudo docker cp /tmp/sermon.py {0}:/tmp/sermon.py'.format(self.dkName))
      self.dkRun('/usr/bin/pip3 install wheel psutil')

    return True

  def getStatus(self):
    '''
    name: SERVER_NAME
    items:
      - name: cpu
        v: 99%
        alertFlag: True

    groups:
      - name: engt
        items:
          - name: err
            v: Error occurs
            alertFlag: True
          - name: ts
            v: 00:21
            alertFlag: False

    '''
    items = []
    groups = []
    if self.status is None:
      return dict(name=self.name, items=[dict(v='loading...')], groups=[])

    for item in self.cfg['monitor']:
      if type(item) == str:
        vv = self.status[item]
        if item == 'cpu':
          items.append(dict(name=item, v='%d%%' % vv, alertFlag=False)) #vv > 80))
        elif item == 'load':
          avg = vv['avg']
          st = '[%d] %.1f,%.1f,%.1f' % (vv['cnt'], avg[0], avg[1], avg[2])
          alertFlag = avg[1] > vv['cnt']*0.8  # 10분간 80%이상
          items.append(dict(name=item, v=st, alertFlag=alertFlag))
        elif item == 'mem':
          st = '%d%%(%dMB)' % (vv['percent'], int(vv['total']/1024/1024))
          items.append(dict(name=item, v=st, alertFlag=vv['percent'] > 90))
        elif item == 'swap':
          st = '%d%%(%dMB)' % (vv['percent'], int(vv['total']/1024/1024))
          items.append(dict(name=item, v=st, alertFlag=vv['percent'] > 90))
        elif item == 'disk':
          st = '%dG/%dG' % (vv['used']/1024/1024/1024, vv['total']/1024/1024/1024)
          items.append(dict(name=item, v=st, alertFlag=vv['free'] < 1024*1024*1024*5))
        else:
          print('unknown item[%s]' % item)

      elif type(item) == dict:
        if item['type'] == 'app':
          name = item['name']
          vv = self.status['apps'][name]
          lst = []
          for v in vv:
            item = vv[v]
            if v == 'ts':
              ts = item
              now = time.time()
              gap = now - ts
              lst.append(dict(name='ts', v=tsGap2str(gap), alertFlag=gap > 60))
            else:
              if type(item) is dict:
                alertFlag = item['alertFlag'] if 'alertFlag' in item else False
                lst.append(dict(name=v, v=str(item['v']), alertFlag=alertFlag))
              else:
                # old style
                lst.append(dict(name=v, v=str(item), alertFlag=False))

          groups.append(dict(name=name, items=lst))

    return dict(name=self.name, items=items, groups=groups)

  def dkRun(self, cmd):
    dkRunUser = '-u %s' % self.dkId if self.dkId is not None else ''
    cmd = 'sudo docker exec -i %s %s %s' % (dkRunUser, self.dkName, cmd)
    return self.ssh.runOutput(cmd)

  def run(self, pk):
    print('%s: cmd - %s' % (self.name, pk))
    if self.dkName is None:
      makeFile(self.ssh, json.dumps(pk), '/tmp/sermon.cmd')
      ss = self.ssh.runOutput('/tmp/sermon.py /tmp/sermon.cmd')
      return json.loads(ss)
    else:
      makeFile(self.ssh, json.dumps(pk), '/tmp/sermon_%s.cmd' % self.dkName)
      self.ssh.run('sudo docker cp /tmp/sermon_{0}.cmd {0}:/tmp/sermon.cmd'.format(self.dkName))
      ss = self.dkRun('/tmp/sermon.py /tmp/sermon.cmd')
      return json.loads(ss)

  def loop(self):
    while True:
      try:
        if not self.isConnected():
          if not self.init():
            continue

        #arr.append(dict(cmd='systemStatus'))
        self.status = self.run(self.cfg['monitor'])
        print('%s: result - %s' % (self.name, self.status))

      except Exception as e:
        print('loop exc - ', traceback.format_exc())
      time.sleep(30)

  def threadStart(self):
    self.thread = threading.Thread(target=self.loop)
    self.thread.start()

class Http:
  def __init__(self, port, loop):
    app = web.Application()
    arr = [
      web.get('/', lambda req: self.httpRoot(req)),
      #web.get('/cmd', lambda req: self.httpCmd(req)),
      web.get('/ws', lambda req: self.httpWs(req)),
    ]
    app.add_routes(arr)

    # chrome에서 cors때문에 접속 안되는 문제
    cors = aiohttp_cors.setup(app)
    resCmd = cors.add(app.router.add_resource("/cmd"))
    opt = aiohttp_cors.ResourceOptions(allow_credentials=False)
    cors.add(resCmd.add_route("POST", lambda req: self.httpCmd(req)), {"*":	opt,})

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

  async def cmdStatus(self, req):
    result = []
    for ser in servers:
      result.append(ser.getStatus())

    return web.Response(text=json.dumps(result))

  async def httpCmd(self, req):
    peername = req.transport.get_extra_info('peername')
    #print('peername - %s' % (peername,))
    host = peername[0]
    port = peername[1]
    allowUse = False
    if host.startswith('127.0.0.'):
      allowUse = True
    elif host == '::1':
      allowUse = True
    elif host.startswith('172.'):
      # 172.16.0.0 ~ 172.31.255.255
      m = re.search(r'^\d+\.(\d+)\.\d+\.\d+', host)
      #n = int(host[4:host.index('.')+4])
      n = int(m.group(1))
      if n >= 16 and n <= 31:
        allowUse = True
    elif host.startswith('192.168.'): #
      allowUse = True
    if not allowUse:
      return web.Response(status=500, text='You can\'t use this API from %s' % host)

    ss = await req.read()	# json
    ss = ss.decode()
    if ss == '':
      return web.Response(status=500, text="invalid request")

    print("http cmd ->", ss)
    pk = json.loads(ss)
    try:
      tt = pk["type"]
      if tt == 'test':
        return web.Response(text="test")
      elif tt == 'status':
        return await self.cmdStatus(req)
      else:
        raise Error('invalid cmd type[%s]' % tt)
    except Error as e:
      return web.Response(text=json.dumps(dict(err='error - %s' % e)))

    except Exception as e:
      self.logE('exc - %s' % e, e)
      return web.Response(text=json.dumps(dict(err='exception - %s' % e)))

  def httpWs(self, req):
    pass

# ctrl+c is not working on windows,(it's fixed in python 3.8)
# https://stackoverflow.com/questions/27480967/why-does-the-asyncios-event-loop-suppress-the-keyboardinterrupt-on-windows
# This restores the default Ctrl+C signal handler, which just kills the process
if os.name == 'nt':
  import signal
  signal.signal(signal.SIGINT, signal.SIG_DFL)


async def checkLoop():
  await asyncio.sleep(20)

  email = Email()
  email.init('smtp.gmail.com', 587, g_cfg['notification']['id'], g_cfg['notification']['pw'])

  errChanged = False
  errList = []  # {name, exist}
  def _errNew(name):
    for err in errList:
      if err['name'] == name:
        err['exist'] = True
        return False
    
    # new error
    errList.append(dict(name=name, exist=True))
    return True

  while True:
    result = []
    for ser in servers:
      result.append(copy.deepcopy(ser.getStatus()))

    #print(result)
    for err in errList:
      err['exist'] = False
    errChanged = False

    notiSubject = ''
    notiCtx = ''
    for ser in result:
      notiCtx += '<br><br>%s - ' % ser['name']

      for item in ser['items']:
        if item.get('alertFlag', False):
          notiCtx += '<font color="red">%s(%s),</font>&nbsp;' % (item['name'], item['v'])
          name = '%s/%s' % (ser['name'], item['name'])
          if _errNew(name):
            print('new err - %s' % name)
            notiSubject = '[ERROR] - %s' % name
            errChanged = True

      for group in ser['groups']:
        notiCtx += '<br>&nbsp;&nbsp;%s - ' % group['name']

        for item in group['items']:
          if item.get('alertFlag', False):
            notiCtx += '<font color="red">%s(%s),</font>&nbsp;' % (item['name'], item['v'])
            name = '%s/%s/%s' % (ser['name'], group['name'], item['name'])
            if _errNew(name):
              print('new err - %s' % (name))
              notiSubject = '[ERROR] - %s' % name
              errChanged = True
            item['new'] = True

    for err in errList:
      if not err['exist']:
        print('no exist - %s' % err['name'])
        notiSubject = '[RECOVER] - %s' % err['name']
        errChanged = True
        break

    errList = list(filter(lambda x: x['exist'], errList))

    if errChanged:
      print('\n\n\nchanged -', errList)
      notiCtx += '<br><br><a href=%s>%s</a>' % (g_cfg['domain'], g_cfg['domain'])
      # removed - errList / exit false
      # new - item.new True
      ##ss = yaml.safe_dump(result)
      email.sendHtml('inertry@gmail.com', g_cfg['notification']['emails'], notiSubject, notiCtx)

    await asyncio.sleep(5)

'''
    name: SERVER_NAME
    items:
      - name: cpu
        v: 99%
        alertFlag: True

    groups:
      - name: engt
        items:
          - name: err
            v: Error occurs
            alertFlag: True
          - name: ts
            v: 00:21
            alertFlag: False
'''

def loadConfig():
  with open('./config/base.yml', "r") as fp:
    ss = fp.read()
  cfg = yaml.safe_load(ss)

  if os.path.exists('./config/my.yml'):
    with open('./config/my.yml', "r") as fp:
      ss = fp.read()

    cfg2 = yaml.safe_load(ss)
    cfg = dictMerge(cfg, cfg2)

  return cfg

def main():
  global g_cfg
  g_cfg = loadConfig()
  ss = '\n'.join(list(map(lambda line: '  '+line, yaml.safe_dump(g_cfg).split('\n'))))
  print('cfg -\n%s' % ss)

  loop = asyncio.get_event_loop()
  http = Http(g_cfg['port'], loop)

  for cc in g_cfg['servers']:
    if 'name' not in cc:
      continue
    
    ser = Server(cc)
    servers.append(ser)
    ser.threadStart()

  #check = Timer(1, dict(http=http), checkFunc)
  asyncio.ensure_future(checkLoop())

  try:
    loop.run_forever()
  except KeyboardInterrupt:
    print('key interrupt')
    pass

if __name__ == "__main__":
  main()


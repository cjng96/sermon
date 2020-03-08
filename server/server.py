#!/usr/bin/python3

import yaml
import time
import json

from coSsh import CoSsh
from myutil import *

servers = []


class Server:
  def __init__(self, ser):
    self.ssh = None
    self.ser = ser

  def isConnected(self):
    return self.ssh is not None

  def init(self):
    if 'docker' in self.ser:
      return False

    arr = self.ser['url'].split(':')
    host = arr[0]
    port = 22
    if len(arr) > 1:
      port = int(arr[1])

    ssh = CoSsh()
    ssh.init(host, port, self.ser['id'])
    self.ssh = ssh

    ssh.uploadFile('./helper.py', '/tmp/sermon.py')
    ssh.run('chmod 755 /tmp/sermon.py')
    return True

  def run(self, pk):
    makeFile(self.ssh, json.dumps(pk), '/tmp/sermon.cmd')
    ss = self.ssh.runOutput('/tmp/sermon.py /tmp/sermon.cmd')
    return json.loads(ss)
    

def main():
  with open('./config/base.yml', "r") as fp:
    ss = fp.read()

  cfg = yaml.safe_load(ss)

  for cc in cfg['servers']:
    ser = Server(cc)
    servers.append(ser)

  while True:
    for ser in servers:
      if not ser.isConnected():
        if not ser.init():
          continue

      result = ser.run(dict(cmd='systemStatus'))
      print('result - %s' % result)
      time.sleep(10)

if __name__ == "__main__":
  main()


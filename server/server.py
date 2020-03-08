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
    self.docker = None
    self.dockerId = None
    self.name = self.ser['name']

  def isConnected(self):
    return self.ssh is not None

  def init(self):
    if 'docker' in self.ser:
      self.docker = self.ser['docker']
      if 'dockerId' in self.ser:
        self.dockerId = self.ser['dockerId']
      else:
        self.dockerId = self.ser['id']


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

    # TODO: virtual env
    if self.docker is None:
      self.ssh.run('/usr/bin/pip3 install wheel psutil')
    else:
      self.ssh.run('sudo docker cp /tmp/sermon.py {0}:/tmp/sermon.py'.format(self.docker))
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

      arr = []
      arr.append(dict(cmd='systemStatus'))
      result = ser.run(dict(arr=arr))
      print('result[%s] - %s' % (ser.name, result))

    time.sleep(10)

if __name__ == "__main__":
  main()


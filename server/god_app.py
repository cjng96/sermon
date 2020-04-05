
import yaml
import string
import random

config = """
type: app
name: sermon
cmd: [ python3, server.py ]

serve:
  patterns: [ "*.go", "*.yml", "*.graphql" ]

deploy:
  strategy: zip
  followLinks: True
  maxRelease: 3
  include:
    - "*"
  exclude:
    - __pycache__
  sharedLinks: []

#defaultVars:

servers:
  - name: release
    host: nas.mmx.kr
    port: 7022
    id: cjng96
    dkName: ser
    dkId: cjng96
    owner: sermon
    deployRoot: /home/{{server.owner}}
    vars:
      domain: sermon.mmx.kr
      webDocker: web
      root: /data/sermon
"""

import os
import sys
provisionPath = os.path.expanduser('~/iner/provision/')
sys.path.insert(0, provisionPath)
import myutil as my

class myGod:
  def __init__(self, helper, **_):
    helper.configStr("yaml", config)
    self.data = helper.loadData(os.path.join(provisionPath, '.data.yml'))

  # return: False(stop post processes)
  def buildTask(self, util, local, **kwargs):
    #local.gqlGen()
    #local.goBuild()
    pass

  def deployPreTask(self, util, remote, local, **_):
    # create new user with ssh key
    #remote.userNew(remote.server.owner, existOk=True, sshKey=True)
    #remote.run('sudo adduser {{remote.server.id}} {{remote.server.owner}}')
    #remote.run('sudo touch {0} && sudo chmod 700 {0}'.format('/home/{{server.owner}}/.ssh/authorized_keys'))
    #remote.strEnsure("/home/{{server.owner}}/.ssh/authorized_keys", local.strLoad("~/.ssh/id_rsa.pub"), sudo=True)
		
		# 현재 user만들고 sv조작때문에 sudo가 필요하다
    pubs = list(map(lambda x: x['key'], self.data.sshPub))
    pubs.append(local.strLoad('~/.ssh/id_rsa.pub'))
    my.makeUser(remote, id=remote.server.owner, authPubs=pubs)
    remote.run('sudo adduser {{server.id}} {{server.owner}}')

  def deployPostTask(self, util, remote, local, **_):
    # web과 server를 지원하는 nginx 설정
    #my.nginxWebSite(remote, name='sermon', domain=remote.vars.domain, certAdminEmail='cjng96@gmail.com', root='%s/current' % remote.server.deployRoot, cacheOn=True)

    remote.run('sudo apt install --no-install-recommends -y libffi-dev')
    remote.run('cd {{deployPath}} && sudo -H pip3 install -r requirements.txt')

    with open('config/base.yml', "r") as fp:
      env = yaml.safe_load(fp.read())

    proxyUrl = 'http://%s:%d' % (remote.server.dkName, env['port'])
    web = remote.otherDockerConn(remote.vars.webDocker, dkId=remote.server.dkId)
    my.setupWebApp(web, name=remote.server.owner, 
      domain=remote.vars.domain, certAdminEmail='cjng96@gmail.com', root='%s/current' % remote.vars.root,
      apiPath='/cmd', proxyUrl=proxyUrl, privateApi='/api/pcmd', privateFilter='''\
allow 172.0.0.0/8; # docker''')

    # register ssh key of sermon
    pub = remote.runOutput('sudo cat /home/%s/.ssh/id_rsa.pub' % remote.server.owner)
    for server in env['servers']:
      arr = server['url'].split(':')
      host = arr[0]
      port = int(arr[1]) if len(arr) >= 2 else 22
      dkName = server.get('dkName', None)
      dkId = server.get('dkId', None)
      ser = remote.remoteConn(host=host, port=port, id=server['id'], dkName=dkName, dkId=dkId)
      my.registerAuthPub(ser, id=dkId, pub=pub)

    # register supervisor
    remote.makeFile('''\
[program:{{server.owner}}]
user={{server.owner}}
directory={{deployRoot}}/current/
command=python3 -u server.py
autostart=true
autorestart=true
stopasgroup=true
environment=home="/home/%(program_name)s",LANG="en_US.UTF-8",LC_ALL="en_US.UTF-8"

stderr_logfile=/var/log/supervisor/%(program_name)s_err.log
stdout_logfile=/var/log/supervisor/%(program_name)s_out.log
stdout_logfile_maxbytes=150MB
stderr_logfile_maxbytes=50MB
stdout_logfile_backups=2
stderr_logfile_backups=2
''', '/etc/supervisor/conf.d/{{server.owner}}.conf', sudo=True)
    remote.run('sudo supervisorctl update && sudo supervisorctl restart {{server.owner}}')

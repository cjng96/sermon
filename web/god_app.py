import yaml
import string
import random
import time

config = """
type: app
name: sermonWeb
cmd: [cmd, flutter, run, -d, chrome]

serve:
  patterns: [ "*.dart" ]

deploy:
  strategy: zip
  followLinks: True
  maxRelease: 3
  include:
    - src: build/web
      dest: .

servers:
  - name: mmx
    host: nas.mmx.kr
    port: 13522
    id: cjng96
    dkName: web
    # dkId: cjng96
    #owner: websert
    deployRoot: /data/sermon
    vars:
      serverUrl: https://sermon.mmx.kr:33/cmd

  - name: egw
    host: sermon.retailtrend.net
    port: 443
    id: ubuntu
    dkName: web
    # dkId: cjng96
    #owner: websert
    deployRoot: /data/sermon
    vars:
      serverUrl: http://sermon.retailtrend.net/cmd
"""

import os, sys

provisionPath = os.path.expanduser("~/iner/provision/")
sys.path.append(provisionPath)
import myutil as my


class myGod:
    def __init__(self, helper, **_):
        helper.configStr("yaml", config)
        self.data = helper.loadData(os.path.join(provisionPath, ".data.yml"))

    # return: False(stop post processes)
    def buildTask(self, util, local, **kwargs):
        # local.gqlGen()
        # local.goBuild()
        pass

    def deployPreTask(self, util, remote, local, **_):
        local.run(
            f"fvm flutter build web --dart-define=SERVER_URL={remote.vars.serverUrl}"
        )

        # create new user with ssh key
        # remote.userNew(remote.server.owner, existOk=True, sshKey=True)
        # remote.run('sudo adduser {{remote.server.id}} {{remote.server.owner}}')
        # remote.run('sudo touch {0} && sudo chmod 700 {0}'.format('/home/{{server.owner}}/.ssh/authorized_keys'))
        # remote.strEnsure("/home/{{server.owner}}/.ssh/authorized_keys", local.strLoad("~/.ssh/id_rsa.pub"), sudo=True)

        # remote.run("sudo mkdir -p {0} && sudo chown cjng96: {0}".format(remote.server.deployRoot))
        remote.run(f"sudo mkdir -p {remote.server.deployRoot}")

        pp = "./build/web/index.html"
        with open(pp, "r") as fp:
            ss = fp.read()

        ss = ss.replace('"main.dart.js"', f'"main.dart.js?v={int(time.time())}"')
        print(ss)
        with open("./build/web/index.html", "w") as fp:
            fp.write(ss)

        # canvaskit is 1979 file
        local.run("touch `find build/web/ -type f`")

    def deployPostTask(self, util, remote, local, **_):

        # my.nginxWebSite(remote, name='sermon', domain=remote.vars.domain, certAdminEmail='cjng96@gmail.com', root='%s/current' % remote.server.deployRoot, cacheOn=True)
        pass

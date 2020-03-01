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
  - name: sample
    host: sample.com
    port: 13522
    id: admin
    dkName: web
    #owner: websert
    deployRoot: /data/sermon
    vars:
      serverUrl: https://sermon.sample.com/cmd

"""

import os, sys

# provisionPath = os.path.expanduser("~/iner/provision/")
# sys.path.append(provisionPath)
import gat.plugin as my


class myGat:
    def __init__(self, helper, **_):
        helper.configStr("yaml", config)
        # self.data = helper.loadData(os.path.join(provisionPath, ".data.yml"))

    # return: False(stop post processes)
    def buildTask(self, util, local, **kwargs):
        # local.gqlGen()
        # local.goBuild()
        pass

    def deployPreTask(self, util, remote, local, **_):
        pp = local.config.srcPath
        # local.run(f"cd {pp}; fvm flutter pub get")
        local.run(
            f"cd {pp};fvm flutter build web --dart-define=SERVER_URL={remote.vars.serverUrl}"
        )

        old = os.path.abspath(os.curdir)
        try:
            os.chdir(local.config.srcPath)

            # create new user with ssh key
            # remote.userNew(remote.server.owner, existOk=True, sshKey=True)
            # remote.run('sudo adduser {{remote.server.id}} {{remote.server.owner}}')
            # remote.run('sudo touch {0} && sudo chmod 700 {0}'.format('/home/{{server.owner}}/.ssh/authorized_keys'))
            # remote.strEnsure("/home/{{server.owner}}/.ssh/authorized_keys", local.strLoad("~/.ssh/id_rsa.pub"), sudo=True)

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
        finally:
            os.chdir(old)

    def deployPostTask(self, util, remote, local, **_):
        # my.nginxWebSite(remote, name='sermon', domain=remote.vars.domain, certAdminEmail='admin@gmail.com', root='%s/current' % remote.server.deployRoot, cacheOn=True)
        pass

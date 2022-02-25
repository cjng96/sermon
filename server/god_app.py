import yaml
import string
import random

config = """
type: app
name: sermon
cmd: [ python3, server.py ]

serve:
  patterns: [ "*.py" ]

deploy:
  strategy: zip
  followLinks: True
  maxRelease: 3
  include:
    - "*"
  exclude:
    - __pycache__
    - config/my.yml
    - "config/base-*.yml"

  sharedLinks: []

defaultVars:
  dkName: sermon

servers:
  - name: mmx
    host: nas.mmx.kr
    port: 7022
    id: cjng96
    # dkName: ser
    # dkId: cjng96
    owner: sermon
    # deployRoot: /home/{{server.owner}}
    deployRoot: /app
    vars:
      domain: sermon.mmx.kr
      webDocker: web
      root: /data/sermon

  - name: rtw
    host: watchmon.ucount.it
    port: 443
    id: ubuntu
    # dkName: ser
    # dkId: cjng96
    # owner: sermon
    # deployRoot: /home/{{server.owner}}
    deployRoot: /app
    vars:
      domain: watchmon.ucount.it
      webDocker: web
      root: /data/sermon

"""

"""
해당 서버에서 
sudo yum install python3-devel
sudo pip3 install psutil

app은 
{"ts": 1645681433, "web": {"v": 3725}, "tcp": {"v": 4239}, "startup": {"v": "7D 16:23"}, "certDays": "-45D"}
v말고 alertFlag=true가 있으면 오류로 처리
"""

import os
import sys

provisionPath = os.path.expanduser("~/iner/provision/")
sys.path.insert(0, provisionPath)
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

    def setupTask(self, util, local, remote, **_):
        baseName, baseVer = my.dockerCoImage(remote)

        dkImg = "sermon"
        dkVer, hash = my.deployCheckVersion(remote, util, dkImg, f"{baseVer}.")
        # base-mmx.yml이 갱신되도 다시 업데이트 해야하나

        def update(env):
            env.run("cd /etc/service && rm -rf sshd cron")

            env.deployApp(
                "./god_app",
                profile=remote.server.name,
                serverOvr=dict(dkName=dkImg + "-con"),
                varsOvr=dict(startDaemon=False, sepDk=True),
            )

            env.copyFile(f"config/base-{remote.server.name}.yml", "/app/current/config/my.yml")

        # 이미지는 모두 동일하고, 환경은 실행할때 변수로 주자
        my.dockerUpdateImage(
            remote,
            baseName=baseName,
            baseVer=baseVer,
            newName=dkImg,
            newVer=dkVer,
            hash=hash,
            func=update,
        )

        if remote.runFlag:
            # create container
            my.dockerRunCmd(
                remote.vars.dkName,
                f"{dkImg}:{dkVer}",
                env=remote,
                net="net",
                extra=f"-e PROFILE={remote.server.name}",
            )
            dk = remote.dockerConn(remote.vars.dkName)

            # 갱신될을수 있으니 매번
            dk.copyFile(f"config/base-{remote.server.name}.yml", "/app/current/config/my.yml")

            # with open(f"config/my.yml", "r") as fp:
            # env = yaml.safe_load(fp.read())
            ss = dk.runOutput("cat /app/current/config/my.yml")
            cfg = yaml.safe_load(ss)

            # register ssh key of sermon - 이거 키 보존해야한다 매번 바뀌면 안됨
            # pub = remote.runOutput(f"sudo cat /home/{remote.server.owner}/.ssh/id_rsa.pub")
            pub = dk.runOutput(f"sudo cat /root/.ssh/id_rsa.pub")
            for server in cfg["servers"]:
                arr = server["url"].split(":")
                host = arr[0]
                port = int(arr[1]) if len(arr) >= 2 else 22
                dkName = server.get("dkName", None)
                dkId = server.get("dkId", None)
                ser = dk.remoteConn(host=host, port=port, id=server["id"], dkName=dkName, dkId=dkId)
                my.registerAuthPub(ser, id=server["id"], pub=pub)

            my.writeRunScript(
                dk,
                cmd="""
cd /app/current
exec python3 -u sermon.py
""",
            )

            proxyUrl = f"http://{remote.vars.dkName}:{cfg['port']}"
            web = remote.dockerConn(remote.vars.webDocker)  # , dkId=remote.server.dkId)
            my.setupWebApp(
                web,
                # name=remote.server.owner,
                name=remote.config.name,
                domain=remote.vars.domain,
                certAdminEmail="cjng96@gmail.com",
                root=f"{remote.vars.root}/current",
                publicApi="/cmd",
                proxyUrl=proxyUrl,
                privateApi="/api/pcmd",
                privateFilter="""\
allow 172.0.0.0/8; # docker""",
                certSetup=remote.server.name != "rtw",
            )

    def deployPreTask(self, util, remote, local, **_):
        # create new user with ssh key
        # remote.userNew(remote.server.owner, existOk=True, sshKey=True)
        # remote.run('sudo adduser {{remote.server.id}} {{remote.server.owner}}')
        # remote.run('sudo touch {0} && sudo chmod 700 {0}'.format('/home/{{server.owner}}/.ssh/authorized_keys'))
        # remote.strEnsure("/home/{{server.owner}}/.ssh/authorized_keys", local.strLoad("~/.ssh/id_rsa.pub"), sudo=True)

        if remote.vars.sepDk:
            my.makeUser(remote, id="sermon", genSshKey=False)
            my.makeUser(remote, id="cjng96", genSshKey=False)
            my.sshKeyGen(remote, id="root")

        else:
            # 현재 user만들고 sv조작때문에 sudo가 필요하다
            pubs = list(map(lambda x: x["key"], self.data.sshPub))
            pubs.append(local.strLoad("~/.ssh/id_rsa.pub"))
            my.makeUser(remote, id=remote.server.owner, authPubs=pubs)
            remote.run(f"sudo adduser {remote.server.id} {remote.server.owner}")

    def deployPostTask(self, util, remote, local, **_):
        # web과 server를 지원하는 nginx 설정
        # my.nginxWebSite(remote, name='sermon', domain=remote.vars.domain, certAdminEmail='cjng96@gmail.com', root='%s/current' % remote.server.deployRoot, cacheOn=True)

        remote.run("sudo apt install --no-install-recommends -y libffi-dev")
        remote.run(f"cd {remote.server.deployPath} && sudo -H pip3 install -r requirements.txt")

        # TODO: my.yml notification.pw를 생성해주자

        if not remote.vars.sepDk:
            # register supervisor
            remote.makeFile(
                """\
[program:{{server.owner}}]
user={{server.owner}}
directory={{deployRoot}}/current/
command=python3 -u sermon.py
autostart=true
autorestart=true
stopasgroup=true
environment=HOME="/home/%(program_name)s",LANG="en_US.UTF-8",LC_ALL="en_US.UTF-8"

stderr_logfile=/var/log/supervisor/%(program_name)s_err.log
stdout_logfile=/var/log/supervisor/%(program_name)s_out.log
stdout_logfile_maxbytes=150MB
stderr_logfile_maxbytes=50MB
stdout_logfile_backups=2
stderr_logfile_backups=2
""",
                f"/etc/supervisor/conf.d/{remote.server.owner}.conf",
                sudo=True,
            )
            remote.run(f"sudo supervisorctl update && sudo supervisorctl restart {remote.server.owner}")

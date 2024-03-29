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
    # - config
    - .vscode

  sharedLinks: []

defaultVars:
  dkName: sermon

servers:
  - name: sample
    host: sample.com
    port: 22
    id: admin
    # dkName: ser
    # dkId: admin
    owner: sermon
    # deployRoot: /home/{{server.owner}}
    deployRoot: /app
    vars:
      domain: sermon.sample.com
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

# provisionPath = os.path.expanduser("~/iner/provision/")
# sys.path.insert(0, provisionPath)

import gat.plugin as my
import gat.myutil as gutil


class myGat:
    def __init__(self, helper, **_):
        helper.configStr("yaml", config)

        # self.data = helper.loadData(os.path.join(provisionPath, ".data.yml"))

    # return: False(stop post processes)
    def buildTask(self, util, local, **_):
        # local.gqlGen()
        # local.goBuild()
        pass

    def setupTask(self, util, local, remote, **_):
        baseName, baseVer = my.dockerCoImage(remote)

        dkImg = "sermon"
        dkVer, hash = my.deployCheckVersion(remote, util, dkImg, f"{baseVer}.")
        # cfg-env.yml이 갱신되도 다시 업데이트 해야하나

        def update(env):
            env.run("cd /etc/service && rm -rf sshd cron")

            env.deployApp(
                # f"{remote.config.srcPath}/gat_app",
                self.rootGatPath,
                profile=remote.server.name,
                serverOvr=dict(dkName=dkImg + "-con"),
                varsOvr=dict(startDaemon=False, sepDk=True),
            )

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
            dk.copyFile(
                f"config/cfg-{remote.server.name}.yml", "/app/current/config/my.yml"
            )
            dk.copyFile(f"config/id_ed25519", "/root/.ssh/id_ed25519", mode="600")
            dk.copyFile(
                f"config/id_ed25519.pub", "/root/.ssh/id_ed25519.pub", mode="600"
            )

            # with open(f"config/my.yml", "r") as fp:
            # env = yaml.safe_load(fp.read())
            ss = dk.runOutput("cat /app/current/config/my.yml")
            cfg = yaml.safe_load(ss)

            # register ssh key of sermon - 이거 키 보존해야한다 매번 바뀌면 안됨
            # pub = remote.runOutput(f"sudo cat /home/{remote.server.owner}/.ssh/id_rsa.pub")
            pub = dk.runOutput(f"cat /root/.ssh/id_ed25519.pub")
            for server in cfg["servers"]:
                arr = server["url"].split(":")
                host = arr[0]
                port = int(arr[1]) if len(arr) >= 2 else 22
                dkName = server.get("dkName", None)
                dkId = server.get("dkId", None)
                ser = dk.remoteConn(
                    host=host,
                    port=port,
                    id=server["id"],
                    dkName=dkName,
                    dkId=dkId,
                    keyFile=server.get("key"),
                )
                my.registerAuthPub(ser, id=server["id"], pub=pub)

            my.writeRunScript(
                dk,
                cmd="""
cd /app/current
exec python3 -u sermon.py
""",
            )

            usingProxy = False

            proxyUrl = f"http://{remote.vars.dkName}:{cfg['port']}"
            web = remote.dockerConn(remote.vars.webDocker)  # , dkId=remote.server.dkId)
            my.setupWebApp(
                web,
                # name=remote.server.owner,
                name=remote.config.name,
                domain=remote.vars.domain,
                certAdminEmail=remote.vars.certAdminEmail,
                root=f"{remote.vars.root}/current",
                publicApi="/cmd",
                proxyUrl=proxyUrl,
                privateApi="/api/pcmd",
                privateFilter="""\
allow 172.0.0.0/8; # docker""",
                # certSetup=remote.server.name != "rtw",
                certSetup=remote.server.name == "__excom",  # eg는 http로 쓴다
                localBind=usingProxy,
            )

            # 이제 n2가 메인이다 - 이제 setupWebApp에서 certSetup직접 함
            if remote.server.name == "__excom" and usingProxy:
                d21 = remote.remoteConn("sample.com", port=20422, id="root")

                # 인증서만 얻어올까? - 어차피 블럭을 추가해버리기 때문에 설정은 있어야한다
                my.setupProxyForNginx(
                    d21,
                    name="sermon",
                    domain=remote.vars.domain,
                    certAdminEmail=remote.vars.certAdminEmail,
                    proxyUrl="http://192.168.111.135",
                    nginxCfgPath="/etc/nginx/sites-enabled",
                    buffering=False,
                )

                # 설정이 없으면 다른 설정에 server block을 추가해버린다
                # certbotSetup(
                #     d21,
                #     domainStr=remote.vars.domain,
                #     email='admin@gmail.com',
                #     name='sermon',
                #     httpRedirect=False,
                #     nginxCfgPath='/etc/nginx/sites-enabled',
                # )

                # 일단 d21 proxy, direct 둘다 지원한다
                # cron으로 주기적으로 가져와야한다
                # ssh root@192.168.1.204
                my.certbotCopy(d21, web, domain=remote.vars.domain, cfgName="sermon")

    def deployPreTask(self, util, remote, local, **_):
        # create new user with ssh key
        # remote.userNew(remote.server.owner, existOk=True, sshKey=True)
        # remote.run('sudo adduser {{remote.server.id}} {{remote.server.owner}}')
        # remote.run('sudo touch {0} && sudo chmod 700 {0}'.format('/home/{{server.owner}}/.ssh/authorized_keys'))
        # remote.strEnsure("/home/{{server.owner}}/.ssh/authorized_keys", local.strLoad("~/.ssh/id_rsa.pub"), sudo=True)

        # 현재 user만들고 sv조작때문에 sudo가 필요하다
        # pubs = list(map(lambda x: x["key"], self.data.sshPub))
        # pubs.append(local.strLoad("~/.ssh/id_ed25519.pub"))
        # my.makeUser(remote, id=remote.server.owner, authPubs=pubs)
        # remote.run(f"sudo adduser {remote.server.id} {remote.server.owner}")
        pass

    def deployPostTask(self, util, remote, local, **_):
        # web과 server를 지원하는 nginx 설정
        # my.nginxWebSite(remote, name='sermon', domain=remote.vars.domain, certAdminEmail='admin@gmail.com', root='%s/current' % remote.server.deployRoot, cacheOn=True)

        remote.run("sudo apt install --no-install-recommends -y libffi-dev")
        remote.run(
            f"cd {remote.server.deployPath} && sudo -H pip3 install -r requirements.txt"
        )

        # TODO: my.yml notification.pw를 생성해주자

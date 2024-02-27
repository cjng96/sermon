## Instruction

- `git init sermon; cd sermon`
- `cp -rf sermon/server/config .`
- `git submodule add git@github.com:cjng96/sermon.git && git submodule update --init`
- `ssh-keygen -t ed25519 -f config/id_ed25519 -N ''`
- create ser_app.py file as follows,

```python
import sys, os
sys.path.insert(0, "sermon/server")
import gat_app as app
import gat.plugin as my

ovrConfig = """
srcPath: sermon/server
servers:
  - name: mmx
    host: nas.mmx.kr
    port: 13522
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


  - name: egw
    host1: watchmon.ucount.it
    host: sermon.retailtrend.net
    port: 443
    id: ubuntu
    # dkName: ser
    # dkId: cjng96
    # owner: sermon
    # deployRoot: /home/{{server.owner}}
    deployRoot: /app
    vars:
      domain: sermon.retailtrend.net
      webDocker: web
      root: /data/sermon

"""

class myGat(app.myGat):
    def __init__(self, helper, **_):
        super().__init__(helper)
        helper.configStr("yaml", ovrConfig)
        self.rootGatPath = os.path.abspath(__file__)
```

- `gat ser_app ENV_NAME run`

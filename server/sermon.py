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
from enum import Enum

from coSsh import CoSsh
from coLog import glog, Error
from myutil import *

from coTime import tsGap2str
from coEmail import Email


servers = []
g_cfg = {}

"""
http post localhost:25090/cmd type=status
"""

# TODO: helper.py 와 sermon.py에 있는 WarningStatus를 어떻게 깔끔하게 처리할지?
class WarningStatus(Enum):
    NORMAL = "n"
    WARNING = "w"
    ERROR = "e"

    def __eq__(self, other):
        if isinstance(other, str):
            return self.value.lower() == other.lower()
        return super().__eq__(other)


class MyCoSsh(CoSsh):
    def __init__(self, name):
        self.name = name

    def log(self, lv, msg):
        print("%d) %s - %s" % (lv, self.name, msg))


class Server:
    def __init__(self, cfg):
        self.ssh = None
        self.cfg = cfg
        self.dkName = None
        self.dkId = None
        self.name = self.cfg["name"]
        self.ts = 0
        print(f"server: {self.name} - {cfg['url']}")

        self.status = None

        if "dkName" in self.cfg:
            self.dkName = self.cfg["dkName"]
            if "dkId" in self.cfg:
                self.dkId = self.cfg["dkId"]
            else:
                self.dkId = self.cfg["id"]

        self.thread = None

    def isConnected(self):
        return self.ssh is not None

    def init(self):
        arr = self.cfg["url"].split(":")
        host = arr[0]
        port = 22
        if len(arr) > 1:
            port = int(arr[1])

        ssh = MyCoSsh(self.name)
        ssh.init(host, port, self.cfg["id"])

        ssh.uploadFile("./helper.py", "/tmp/sermon.py")
        ssh.run("chmod 755 /tmp/sermon.py")

        self.ssh = ssh

        # TODO: virtual env
        if self.dkName is None:
            try:
                ssh.run("/usr/bin/pip3 install wheel psutil")
            except Exception as e:
                ssh.run("/usr/bin/pip3 install --break-system-packages wheel psutil")

        else:
            ssh.run(f"sudo docker cp /tmp/sermon.py {self.dkName}:/tmp/sermon.py")
            try:
                self.dkRun("/usr/bin/pip3 install wheel psutil")
            except Exception as e:
                self.dkRun("/usr/bin/pip3 install --break-system-packages wheel psutil")

        return True

    def getStatus(self):
        """
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

        """
        items = []
        groups = []
        if self.status is None:
            return dict(
                name=self.name, items=[dict(name="loading", v="...")], groups=[]
            )

        for item in self.cfg["monitor"]:
            if type(item) == str:
                vv = self.status[item]
                if item == "newline":
                    items.append(dict(name="newline", type="sp"))
                elif item == "cpu":
                    items.append(
                        dict(name=item, v="%.1f%%" % vv, alertFlag=WarningStatus.NORMAL.value)
                    )  # vv > 80))
                elif item == "load":
                    avg = vv["avg"]
                    st = "[%d] %.1f,%.1f,%.1f" % (vv["cnt"], avg[0], avg[1], avg[2])

                    alertFlag = WarningStatus.NORMAL.value
                    if avg[1] > vv["cnt"] * 0.8:    # 10분간 80%이상
                       alertFlag = WarningStatus.WARNING.value
                    elif avg[1] > vv["cnt"] * 0.9:  # 10분간 90%이상
                        alertFlag = WarningStatus.ERROR.value
                    items.append(dict(name=item, v=st, alertFlag=alertFlag))
                elif item == "mem":
                    st = "%d%%(%dMB)" % (vv["percent"], int(vv["total"] / 1024 / 1024))
                    alertFlag = WarningStatus.NORMAL.value
                    if vv["percent"] > 95:
                        alertFlag = WarningStatus.ERROR.value
                    elif vv["percent"] > 90:
                        alertFlag = WarningStatus.WARNING.value

                    items.append(dict(name=item, v=st, alertFlag=alertFlag))
                elif item == "swap":
                    st = "%d%%(%dMB)" % (vv["percent"], int(vv["total"] / 1024 / 1024))
                    alertFlag = WarningStatus.NORMAL.value
                    if vv["percent"] > 95:
                        alertFlag = WarningStatus.ERROR.value
                    elif vv["percent"] > 90:
                        alertFlag = WarningStatus.WARNING.value

                    items.append(dict(name=item, v=st, alertFlag=alertFlag))
                elif item == "disk":
                    st = "%dG/%dG" % (
                        vv["used"] / 1024 / 1024 / 1024,
                        vv["total"] / 1024 / 1024 / 1024,
                    )

                    alertFlag = WarningStatus.NORMAL.value
                    free_percentage = (vv["free"] / vv["total"]) * 100

                    if free_percentage < 5:
                        alertFlag = WarningStatus.ERROR.value
                    elif free_percentage < 10:
                        alertFlag = WarningStatus.WARNING.value

                    items.append(
                        dict(
                            name=item,
                            v=st,
                            alertFlag=alertFlag
                        )
                    )
                else:
                    print("unknown item[%s]" % item)

            elif type(item) == dict:
                tt = item["type"]
                if tt == "disk":
                    name = item["name"]
                    vv = self.status["disks"][name]

                    st = "%dG/%dG" % (
                        vv["used"] / 1024 / 1024 / 1024,
                        vv["total"] / 1024 / 1024 / 1024,
                    )

                    alertFlag = WarningStatus.NORMAL.value
                    free_percentage = (vv["free"] / vv["total"]) * 100

                    if free_percentage < 5:
                        alertFlag = WarningStatus.ERROR.value
                    elif free_percentage < 10:
                        alertFlag = WarningStatus.WARNING.value

                    items.append(
                        dict(
                            name=name,
                            v=st,
                            alertFlag=alertFlag
                        )
                    )
                elif tt == "mdadm":
                    name = item["name"]
                    vv = self.status["mdadms"][name]

                    st = "%d/%d" % (vv["act"], vv["tot"])

                    alertFlag = WarningStatus.NORMAL.value
                    if vv["act"] != vv["tot"]:
                        alertFlag = WarningStatus.ERROR.value

                    items.append(
                        dict(name=name, v=st, alertFlag=alertFlag)
                    )

                elif tt == "app":
                    name = item["name"]
                    vv = self.status["apps"][name]
                    lst = []

                    # ts먼저 처리
                    ts = vv.get("ts")
                    if ts is not None:
                        now = time.time()
                        gap = now - ts
                        alertFlag = WarningStatus.NORMAL.value
                        if gap > 60:
                            alertFlag = WarningStatus.ERROR.value
                        lst.append(
                            dict(name="ts", v=tsGap2str(gap), alertFlag=alertFlag)
                        )

                    for key in vv:
                        item = vv[key]
                        if key == "ts":
                            continue
                        elif key == "arr":
                            for node in item:
                                alertFlag = getAlertFlag(node)
                                lst.append(
                                    dict(
                                        name=node["n"],
                                        v=str(node["v"]),
                                        alertFlag=alertFlag
                                    )
                                )
                        else:
                            if type(item) is dict:
                                # alertFlag = item["alertFlag"] if "alertFlag" in item else False
                                alertFlag = getAlertFlag(item)
                                lst.append(
                                    dict(
                                        name=key, v=str(item["v"]), alertFlag=alertFlag
                                    )
                                )
                            else:
                                # old style
                                lst.append(dict(name=key, v=str(item), alertFlag=WarningStatus.NORMAL.value))

                    groups.append(dict(name=name, items=lst))

        return dict(name=self.name, ts=int(self.ts), items=items, groups=groups)

    def dkRunCmd(self, cmd):
        dkRunUser = "-u %s" % self.dkId if self.dkId is not None else ""
        cmd = "sudo docker exec -i %s %s %s" % (dkRunUser, self.dkName, cmd)
        return cmd

    def dkRun(self, cmd):
        cmd = self.dkRunCmd(cmd)
        return self.ssh.runOutput(cmd)

    def run(self, pk):
        print(f"{self.name}: cmd - {pk}")
        for i in range(3):
            try:
                if self.dkName is None:
                    # makeFile(self.ssh, json.dumps(pk), '/tmp/sermon.cmd')
                    # ss = self.ssh.runOutput('/tmp/sermon.py /tmp/sermon.cmd')
                    cmd = makeFileCmd(json.dumps(pk), "/tmp/sermon.cmd")
                    cmd += " && /tmp/sermon.py /tmp/sermon.cmd"
                    ss = self.ssh.runOutput(cmd)
                    return json.loads(ss)
                else:
                    # 아래 세개 명령을 합쳐서 한번에 수행하자 - 얼마나 차이날라나 2.35 -> 2.13
                    # makeFile(self.ssh, json.dumps(pk), '/tmp/sermon_%s.cmd' % self.dkName)
                    # self.ssh.run('sudo docker cp /tmp/sermon_{0}.cmd {0}:/tmp/sermon.cmd'.format(self.dkName))
                    # ss = self.dkRun('/tmp/sermon.py /tmp/sermon.cmd')
                    cmd = makeFileCmd(json.dumps(pk), f"/tmp/sermon_{self.dkName}.cmd")
                    cmd += " && "
                    cmd += f"sudo docker cp /tmp/sermon_{self.dkName}.cmd {self.dkName}:/tmp/sermon.cmd"
                    cmd += " && "
                    cmd += self.dkRunCmd("/tmp/sermon.py /tmp/sermon.cmd")
                    ss = self.ssh.runOutput(cmd)
                    return json.loads(ss)
            except Exception:
                if i == 2:
                    raise

                # File "/usr/local/lib/python3.8/dist-packages/paramiko/transport.py", line 1013, in open_channel
                # raise SSHException("SSH session not active")
                # paramiko.ssh_exception.SSHException: SSH session not active
                self.init()

    def loop(self):
        while True:
            try:
                if not self.isConnected():
                    if not self.init():
                        continue

                # arr.append(dict(cmd='systemStatus'))
                self.status = self.run(self.cfg["monitor"])
                self.ts = time.time()
                print(f"{self.name}: result - {self.status}")

            except Exception as e:
                print(f"{self.name}: loop exc - ", traceback.format_exc())
            time.sleep(30)

    def threadStart(self):
        self.thread = threading.Thread(target=self.loop)
        self.thread.start()


class Http:
    def __init__(self, port, loop):
        app = web.Application()
        arr = [
            web.get("/", lambda req: self.httpRoot(req)),
            # web.get('/cmd', lambda req: self.httpCmd(req)),
            web.get("/ws", lambda req: self.httpWs(req)),
        ]
        app.add_routes(arr)

        # chrome에서 cors때문에 접속 안되는 문제
        cors = aiohttp_cors.setup(app)
        resCmd = cors.add(app.router.add_resource("/cmd"))
        opt = aiohttp_cors.ResourceOptions(allow_credentials=False)
        cors.add(
            resCmd.add_route("POST", lambda req: self.httpCmd(req)),
            {
                "*": opt,
            },
        )
        cors.add(
            resCmd.add_route("GET", lambda req: self.httpCmd(req)),
            {
                "*": opt,
            },
        )

        runner = web.AppRunner(app)
        loop.run_until_complete(runner.setup())
        # await runner.cleanup()

        site = aiohttp.web.TCPSite(runner, "", port)
        # self.log(1, 'http server - %d' % (port))
        loop.run_until_complete(site.start())
        self.log(1, "http: server start with port[%d]" % port)

    def log(self, lv, ss, noti=None):
        glog.log(lv, "http: %s" % ss, noti)

    def logE(self, msg, e, noti=None):
        glog.exc("http: %s" % msg, e, noti)

    def httpRoot(self, req):
        return web.Response(text="hello")

    async def cmdStatus(self, req):
        results = []
        for ser in servers:
            results.append(ser.getStatus())

        # return web.Response(text=json.dumps(result))
        return web.json_response(
            {"name": g_cfg["name"], "fixedFont": g_cfg["fixedFont"], "servers": results}
        )

    async def httpCmd(self, req):
        peername = req.transport.get_extra_info("peername")
        # print('peername - %s' % (peername,))
        host = peername[0]
        port = peername[1]
        allowUse = False
        if host.startswith("127.0.0."):
            allowUse = True
        elif host == "::1":
            allowUse = True
        elif host.startswith("172."):
            # 172.16.0.0 ~ 172.31.255.255
            m = re.search(r"^\d+\.(\d+)\.\d+\.\d+", host)
            # n = int(host[4:host.index('.')+4])
            n = int(m.group(1))
            if n >= 16 and n <= 31:
                allowUse = True
        elif host.startswith("192.168."):  #
            allowUse = True
        if not allowUse:
            return web.Response(
                status=500, text="You can't use this API from %s" % host
            )

        ss = await req.read()  # json
        ss = ss.decode()
        if ss == "":
            query = req.rel_url.query
            print(f"http cmd(query) -> ${query}")
            cmdType = query.get("type")
            if cmdType is None:
                return web.Response(status=500, text="invalid request")

            pk = {"type": cmdType}
        else:
            print("http cmd(body) ->", ss)
            pk = json.loads(ss)

        try:
            tt = pk["type"]
            if tt == "test":
                return web.Response(text="test")
            elif tt == "status":
                return await self.cmdStatus(req)
            else:
                raise Error("invalid cmd type[%s]" % tt)

        except Error as e:
            # return web.Response(text=json.dumps(dict(err="error - %s" % e)))
            return web.json_response(dict(err="error - %s" % e))

        except Exception as e:
            self.logE("exc - %s" % e, e)
            # return web.Response(text=json.dumps(dict(err="exception - %s" % e)))
            return web.json_response(dict(err="exception - %s" % e))

    def httpWs(self, req):
        pass


# ctrl+c is not working on windows,(it's fixed in python 3.8)
# https://stackoverflow.com/questions/27480967/why-does-the-asyncios-event-loop-suppress-the-keyboardinterrupt-on-windows
# This restores the default Ctrl+C signal handler, which just kills the process
if os.name == "nt":
    import signal

    signal.signal(signal.SIGINT, signal.SIG_DFL)


async def checkLoop():
    await asyncio.sleep(20)

    email = Email()
    email.init(
        "smtp.gmail.com", 587, g_cfg["notification"]["id"], g_cfg["notification"]["pw"]
    )

    errChanged = False
    errList = []  # {name, exist}

    def _errNew(name):
        for err in errList:
            if err["name"] == name:
                err["exist"] = True
                return False

        # new error
        errList.append(dict(name=name, exist=True))
        return True

    while True:
        result = []
        for ser in servers:
            result.append(copy.deepcopy(ser.getStatus()))

        # print(result)
        for err in errList:
            err["exist"] = False
        errChanged = False

        notiSubject = ""
        notiCtx = ""
        for ser in result:
            notiCtx += "<br><br>%s - " % ser["name"]

            for item in ser["items"]:
                alertFlag = getAlertFlag(item)
                fontColor = getErrCr(alertFlag, "black")
                notiCtx += '<span style="color: %s;">%s(%s),</span>&nbsp;' % (
                            fontColor,
                            item["name"],
                            item["v"],
                        )

                if alertFlag == WarningStatus.ERROR.value:
                    name = "%s/%s" % (ser["name"], item["name"])
                    if _errNew(name):
                        print("new err - %s" % name)
                        notiSubject = "[ERROR] - %s" % name
                        errChanged = True

            for group in ser["groups"]:
                notiCtx += "<br>&nbsp;&nbsp;%s - " % group["name"]

                for item in group["items"]:
                    alertFlag = getAlertFlag(item)
                    fontColor = getErrCr(alertFlag, "black")
                    notiCtx += '<span style="color: %s;">%s(%s),</span>&nbsp;' % (
                            fontColor,
                            item["name"],
                            item["v"],
                        )
                    if alertFlag == WarningStatus.ERROR.value:
                        name = "%s/%s/%s" % (ser["name"], group["name"], item["name"])
                        if _errNew(name):
                            print("new err - %s" % (name))
                            notiSubject = "[ERROR] - %s" % name
                            errChanged = True
                        item["new"] = True

        for err in errList:
            if not err["exist"]:
                print("no exist - %s" % err["name"])
                notiSubject = "[RECOVER] - %s" % err["name"]
                errChanged = True
                break

        errList = list(filter(lambda x: x["exist"], errList))

        if errChanged:
            print("\n\n\nchanged -", errList)
            notiCtx += "<br><br><a href=%s>%s</a>" % (g_cfg["domain"], g_cfg["domain"])
            # removed - errList / exit false
            # new - item.new True
            ##ss = yaml.safe_dump(result)
            email.sendHtml(
                "sermon@sermon.com",
                g_cfg["notification"]["emails"],
                notiSubject,
                notiCtx,
            )

        await asyncio.sleep(5)

"""
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
"""


def loadConfig():
    with open("./config/base.yml", "r") as fp:
        ss = fp.read()
    cfg = yaml.safe_load(ss)

    if os.path.exists("./config/my.yml"):
        with open("./config/my.yml", "r") as fp:
            ss = fp.read()

        cfg2 = yaml.safe_load(ss)
        cfg = dictMerge(cfg, cfg2)

    return cfg


def main():
    global g_cfg
    g_cfg = loadConfig()
    ss = "\n".join(
        list(map(lambda line: "  " + line, yaml.safe_dump(g_cfg).split("\n")))
    )
    print("cfg -\n%s" % ss)

    loop = asyncio.get_event_loop()
    http = Http(g_cfg["port"], loop)

    for cc in g_cfg["servers"]:
        if "name" not in cc:
            continue

        ser = Server(cc)
        servers.append(ser)
        ser.threadStart()

    # check = Timer(1, dict(http=http), checkFunc)
    asyncio.ensure_future(checkLoop())

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("key interrupt")
        pass


if __name__ == "__main__":
    main()

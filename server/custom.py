import os, sys
import json
import asyncio
import psutil
import subprocess


def custom(params):
    cmd = params["cmd"]
    if cmd == "mdadmStatus":
        pass

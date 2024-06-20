def str2arg(ss):
    """
    기본적으로 ""로 감쌌다고 가정하고 랩핑한다.
    """
    ss = ss.replace("\\", "\\\\")
    ss = ss.replace('"', '\\"')
    ss = ss.replace("$", "\\$")  # .replace('&', '\&')#.replace('%', '\%')
    # ss = ss.replace("!", "\!")	# echo 문자열 내에 있을때는 안해도 되네...
    ss = ss.replace("[^a-zA-Z]!", "\\!")  # a!는 변환하고 3!는 변환하지 말것
    ss = ss.replace("`", "\\`")  # bash -c "echo '`'" 이거 오류난다.
    return ss


def makeFileCmd(content, path, sudo=False, mode=755):
    content = str2arg(content)

    sudoCmd = "sudo" if sudo else ""
    cmd = 'echo "{1}" | {0} tee {2} > /dev/null && {0} chmod {3} {2}'.format(
        sudoCmd, content, path, mode
    )
    return cmd


def makeFile(ssh, content, path, sudo=False, mode=755):
    cmd = makeFileCmd(content, path, sudo, mode)
    ssh.run(cmd)


import copy

# import collections
from collections.abc import Mapping

from sermon import WarningStatus


# https://gist.github.com/angstwad/bf22d1822c38a92ec0a9
def dictMerge(dic, dic2):
    newDic = {}
    for k, v in dic.items():
        if k not in dic2:
            newDic[k] = copy.deepcopy(v)

    for k, v in dic2.items():
        if k in dic and isinstance(dic[k], dict) and isinstance(dic2[k], Mapping):
            newDic[k] = dictMerge(dic[k], dic2[k])
        else:
            newDic[k] = copy.deepcopy(dic2[k])

    return newDic

# alertFlag 값을 "e", "n", "w"로 변환해주는 함수
def getAlertFlag(item):
    alertFlag = item.get("alertFlag", WarningStatus.NORMAL.value)
    if isinstance(alertFlag, bool):
        alertFlag = WarningStatus.ERROR.value if alertFlag else WarningStatus.NORMAL.value
    return alertFlag

# alertFlagl에 따라 빨강, 밝은 주황, defaultColor return
def getErrCr(alertFlag, defaultColor):
    if alertFlag == WarningStatus.ERROR.value:
        return 'red'
    elif alertFlag == WarningStatus.WARNING.value:
        return '#FFAA00'
    else:
        return defaultColor
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

# alertLevel에 따라 빨강, 밝은 주황, 검은색 return
def getErrCr(alertLevel, defaultColor):
    if alertLevel >= 2:
        return 'red'
    elif alertLevel == 1:
        return '#FFAA00'
    else:
        return defaultColor
    
# alertFlag와 호환을 위환 색상 추출 함수
# @Depreciate:  alertFlag가 alertLevel로 완전히 대체되면 사라질 함수 
def getErrCrForAlertFlag(alertFlag, alertLevel, defaultColor):
    if alertFlag or alertLevel:
         # alertFlag값과 alertLevel 둘 다 있는 경우
        if alertFlag and alertLevel > 0:
            return getErrCr(alertLevel, defaultColor)

        # alertFlag만 있는 경우
        if alertFlag and alertLevel == 0:
            return 'red'

        # alertLevel만 있는 경우
        if not alertFlag and alertLevel > 0:
            return getErrCr(alertLevel)

    return defaultColor
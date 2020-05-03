
def str2arg(ss):
	'''
	기본적으로 ""로 감쌌다고 가정하고 랩핑한다.
	'''
	ss = ss.replace('\\', '\\\\')
	ss = ss.replace('"', '\\"')
	ss = ss.replace('$', '\\$')	#.replace('&', '\&')#.replace('%', '\%')
	#ss = ss.replace("!", "\!")	# echo 문자열 내에 있을때는 안해도 되네...
	ss = ss.replace('[^a-zA-Z]!', '\\!')	# a!는 변환하고 3!는 변환하지 말것
	ss = ss.replace('`', '\\`')	# bash -c "echo '`'" 이거 오류난다.
	return ss

def makeFile(ssh, content, path, sudo=False, mode=755):
  #self.onlyRemote()
  #ss = content.replace('"', '\\"').replace('%', '\%').replace('$', '\$')
  content = str2arg(content)

  sudoCmd = 'sudo' if sudo else ''
  ssh.run('echo "{1}" | {0} tee {2} > /dev/null && {0} chmod {3} {2}'.format(sudoCmd, content, path, mode))

import copy
import collections

# https://gist.github.com/angstwad/bf22d1822c38a92ec0a9
def dictMerge(dic, dic2):
	newDic = {}
	for k, v in dic.items():
		if k not in dic2:
			newDic[k] = copy.deepcopy(v)

	for k, v in dic2.items():
		if (k in dic and isinstance(dic[k], dict) and isinstance(dic2[k], collections.Mapping)):
			newDic[k] = dictMerge(dic[k], dic2[k])
		else:
			newDic[k] = copy.deepcopy(dic2[k])

	return newDic

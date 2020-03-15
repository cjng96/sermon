
import os, sys, traceback
import datetime


# callstack을 찍을 필요 없는 일반적인 경우 - 이거는 slack alert로 안 알린다.
class Error(Exception):
	pass

# http://stackoverflow.com/questions/6086976/how-to-get-a-complete-exception-stack-trace-in-python
def formatExcFull(e):
	#exc = sys.exc_info() E exc_type, exc_value, exc_tb
	exc_type = type(e)
	exc_value = e
	exc_tb = e.__traceback__
	excList = traceback.format_stack()
	excList = excList[:-4]
	excList.append("-------------------\n")
	excList.extend(traceback.format_tb(exc_tb))
	excList.extend(traceback.format_exception_only(exc_type, exc_value))

	excStr = "Traceback (most recent call last):\n"
	excStr += "".join(excList)
	# Removing the last \n
	excStr = excStr[:-1]

	return excStr

def myFormatExc(e):
	#ss = traceback.format_exc()
	ss = formatExcFull(e)
	return ss

class Log:
  def __init__(self):
    self.logPath = None
    self.fp = None
    self.uncatchedHandler = None

    #self.slackAlert = None
    self.notiCb = None  # (msg)

    self.isTestMode = True
    self.isWin32 = False  # 이거 꼭 있어야하나

    # 내부용
    self.today = datetime.date.fromtimestamp(0)

  def initPath(self, logPath):
    self.logPath = logPath
    if logPath is not None:
      if not os.path.exists(logPath):
        os.makedirs(logPath)

  def initNoti(self, notiCb):
    self.notiCb = notiCb

  def _log(self, lv, msg, printOnly=False):
    #timeStr = datetime.datetime.now().strftime("%y-%m%d %H:%M:%S")
    timeStr = datetime.datetime.now().strftime("%m%d %H%M%S")
    if self.isTestMode:
      timeStr += "t"

    today = datetime.date.today()
    if self.logPath is not None and self.today != today:
      oldDay = self.today
      self.today = today
      dd = today.strftime("%y-%m%d")

      if self.fp is not None:
        self.fp.close()

      self.fp = open(os.path.join(self.logPath, dd+".log"), 'a+', 1, encoding="utf8")

      if oldDay != datetime.date.fromtimestamp(0):
        self._log(1, "********************** date is changed to %s........." % dd)

    #msg = msg.replace(codecs.BOM_UTF8.encode(), '')
    try:
      ss = "%d)%s %s" % (lv, timeStr, msg)
      if self.fp is not None and not self.isWin32 and not printOnly:	# no save on win32 for debugging
        self.fp.write(ss+"\n")

      print(ss)
    except Exception as e:
      if self.isWin32:
        return

      """
      with open("/tmp/noti", 'a+') as fp:
        if fp.tell() > 1024*200:
          fp.seek(0)
          fp.truncate(0)

        tstr = datetime.datetime.now().strftime("%m%d %H:%M%S")
        fp.write("%s %s) print err - %s\n" % (tstr, g.name, e))
      """

  def _exc(self, msg, e):
    ss = myFormatExc(e)
    self.log(0, "exception - %s\n%s" % (msg, ss))

  '''
  obj - getLogName를 오버라이딩해야한다.

  '''
  def log(self, lv, ss, noti=None):
    #msg = "%s: %s" % (name, ss)
    self._log(lv, ss)
    if noti == True or (lv == 0 and noti is None):
      if self.notiCb is not None:
        #attach = dict(title="unhandled exception", color="alert", text=ss)
        #gLog.slackAlert.noti("%s log[%d] - %s" % (timeStr, lv, msg), None, noVerbose=True)
        self.notiCb(lv, ss)

  def exc(self, msg, e, noti=None):
    ##ss = traceback.format_exc()
    ss = myFormatExc(e)

    if isinstance(e, Error) and noti is None:
      noti=False

    self.log(0, "exception - %s\n%s" % (msg, ss), noti)

glog = Log()

def _onException(exc_type, exc_value, exc_traceback):
	if issubclass(exc_type, KeyboardInterrupt):
		sys.__excepthook__(exc_type, exc_value, exc_traceback)

	ss = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
	glog.log(0, "--- unhandled exception\n%s" % ss)

	if glog.uncatchedHandler is not None:
		glog.uncatchedHandler(exc_type, exc_value, exc_traceback)

	#sys.__excepthook__(exc_type, exc_value, exc_traceback)

# 콜스택출력까지는 알아서 해준다 cusHandler는 추가 액션이 필요한 경우에 넣으면 된다.
def initExceptionHook(cusHandler=None):
	glog.uncatchedHandler = cusHandler
	sys.excepthook = _onException

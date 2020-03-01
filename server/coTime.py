
def tsGap2str(ts):
  hours = int(ts / (60*60))
  ts -= hours*60*60
  mins = int(ts / 60)
  ts -= mins*60
  secs = ts

  ss = ''
  if hours > 0:
    ss += '%dH ' % hours
  ss += '%02d:%02d' % (mins, secs)
  return ss

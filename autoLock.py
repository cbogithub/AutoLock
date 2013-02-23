import argparse
import cv
import signal
import sys
import time


from faceRecognition import *
import batteryStatus
import ignoreoutput
import lockScreen


DEFAULT_TIME_UNTIL_LOCK = 10
WINDOW_NAME = "AutoLock"
TIME_BETWEEN_FACE_CHECKS = 0.1
TIME_BETWEEN_LOCKS = 100
SLEEP_TIME_WHEN_NOT_CHARGING = 600  # 10 minutes

parser = argparse.ArgumentParser(description=("Automatically lock your screen "
                                              "when not inin range"))
parser.add_argument('--displayWebcam', action='store_const', const=True,
                    help="determies if the image from the webcam is displayed")
parser.add_argument("--runWithDischargingBattery", action='store_const', const=True,
                      help=("if this flag is specified, the program will run even"
                            "when the battery is discharging"))
parser.add_argument("-timeUntilLock", type=int, default=DEFAULT_TIME_UNTIL_LOCK,
                    help=("Time in seconds since the last time a face is detected"
                          "to the time the screen is locked. "
                          "Default value %d seconds." %DEFAULT_TIME_UNTIL_LOCK))
parser.add_argument("-frequency", type=float, default=TIME_BETWEEN_FACE_CHECKS,
                    help=("Time in seconds between face checks. Note that a small"
                          "number increases CPU usage but gives more accuracy."
                          "A big number might imply that the screen locks, "
                          "even though you are in front of the computer. "
                          "Default value %f seconds" %TIME_BETWEEN_FACE_CHECKS))
parser.add_argument("-minTimeBetweenLocks", type=float, default=TIME_BETWEEN_LOCKS,
                    help=("Minimal time in seconds between screen locks."
                          "Default value %f seconds" %TIME_BETWEEN_LOCKS))


args = parser.parse_args()
displayCam = args.displayWebcam
runWithDischargingBattery = args.runWithDischargingBattery
timeUntilLock = args.timeUntilLock
frequency = args.frequency
minTimeBetweenLocks = args.minTimeBetweenLocks

if frequency >= timeUntilLock:
  print ("The time between face detection checks is bigger than the time "
         "until lock. This would result in locking the screen regardless "
         "of someone's presence in front of the screen.")
  print ("As a consequence, defaulting the time between face checks "
         "to half of the time until the screen is locked when no face is detected.")

frequency = timeUntilLock / 2

# When user presses Control-C, gracefully exit program
def signal_handler(signal, frame):
  print "AutoLock will terminate."
  sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


def getCameraCapture():
  with ignoreoutput.suppress_stdout_stderr():
  # -1 is supposed to detected any webcam connected to the device
    return cv.CaptureFromCAM(-1)


def lockWhenFaceNotDetected(timeUntilLock, display=False):

  def oneCycleFaceDetection(lastTimeLocked):
    capture = getCameraCapture()
    currentTime = time.time()
    lastTimeDetected = currentTime
    batteryDischarging = -1
    while currentTime - lastTimeDetected < timeUntilLock:
      currentTime = time.time()
      if not runWithDischargingBattery:
        if not batteryStatus.isCharging():
          if batteryDischarging > 0:
            if currentTime - batteryDischarging > timeUntilLock:
              break
          else:
            batteryDischarging = currentTime
        else:
          batteryDischarging = -1
      frame = cv.QueryFrame(capture)
      if display:
        cv.ShowImage(WINDOW_NAME, frame)
        cv.WaitKey(100)
      faces = getFaces(frame)
      if faces:
        lastTimeDetected = currentTime
      time.sleep(frequency)
    if currentTime - lastTimeLocked > minTimeBetweenLocks:
      lastTimeLocked = currentTime
      lockScreen.lockScreen()
    return lastTimeLocked

  currentTime = time.time()
  lastTimeLocked = currentTime - minTimeBetweenLocks

  if display:
    cv.NamedWindow(WINDOW_NAME, cv.CV_WINDOW_AUTOSIZE)


# if you the battery just started discharging, complete the current cycle
# and then sleep (or just check for a face for 1 seconds at more frequent changes)
# and then lock
#  Note that currently people can put thesmelves in front of the camera,
# so this is not a major issue, but it will become later when
# the face recognition will work for the owner of the computer
# A password should be then asked when the program is started such that
# we avoid a foreigner getting the face recognized with it


  while True:
    # Unless the user specified otherwise, do not run while machine is not
    # not charging
    currentTime = time.time()
    if not runWithDischargingBattery:
      while not batteryStatus.isCharging():
        time.sleep(SLEEP_TIME_WHEN_NOT_CHARGING)

    lastTimeLocked = oneCycleFaceDetection(lastTimeLocked)


def main():
  global timeUntilLock
  if batteryStatus.isCharging() or runWithDischargingBattery:
    if runWithDischargingBattery:
      print "You chose to run AutoLock with your laptop not plugged in"
      print "Be aware of your battery"
    if timeUntilLock < 1:
      print ("timeUntilLock has to be a positive integer, as it represents"
             "the number of seconds since a face was detected to the time the "
             "screen gets locked")
      print "Defaulting to %d seconds" %(DEFAULT_TIME_UNTIL_LOCK)
      timeUntilLock = DEFAULT_TIME_UNTIL_LOCK
    lockWhenFaceNotDetected(timeUntilLock, displayCam)
  else:
    print "Your machine is not charging, AutoLock will not execute"


if __name__ == '__main__':
  main()

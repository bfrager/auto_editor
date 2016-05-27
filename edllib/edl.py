__author__ = 'bjarrett'


NEW_LINE = '\n'

class TimeCode(object):
    DEFAULT_FRAME_RATE = 24

    def __init__(self, hours, minutes, seconds, frames, frameRate=DEFAULT_FRAME_RATE):
        super(TimeCode, self).__init__()
        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds
        self.frames = frames
        self.frameRate = frameRate

    @classmethod
    def fromFrame(cls, frame, frameRate=DEFAULT_FRAME_RATE):
        frames = frame % frameRate
        seconds = (frame / frameRate) % 60
        minutes = (frame / frameRate / 60) % 60
        hours = (frame / frameRate / 60**2) % 60
        return cls(hours, minutes, seconds, frames, frameRate)

    @classmethod
    def fromString(cls, stringRep, frameRate=DEFAULT_FRAME_RATE):
        hours, minutes, seconds, frames = [int(x) for x in stringRep.split(':')]
        return cls(hours, minutes, seconds, frames, frameRate=frameRate)

    def toSeconds(self):
        frameSecs = self.frames * (1./self.frameRate)
        secondSecs = self.seconds
        minuteSecs = self.minutes * 60
        hourSecs = self.hours * 60 ** 2
        return frameSecs + secondSecs + minuteSecs + hourSecs

    def toFrames(self):
        frameFrames = self.frames
        secondFrames = self.seconds * self.frameRate
        minuteFrames = self.minutes * 60 * self.frameRate
        hourFrames = self.hours * 60 ** 2 * self.frameRate
        return frameFrames + secondFrames + minuteFrames + hourFrames

    def __str__(self):
        return '%02d:%02d:%02d:%02d' % (
            self.hours,
            self.minutes,
            self.seconds,
            self.frames,
        )

    def __repr__(self):
        return '<%s: %s>'% (self.__class__.__name__, str(self))

class Clip(object):
    def __init__(self, name):
        super(Clip, self).__init__()
        self.name = name
        self.startTc = None
        self.duration = None

    def __eq__(self, other):
        if other is None:
            return False
        return self.name == other.name

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.name)

class Event(object):
    def __init__(self, reel, eventType):
        super(Event, self).__init__()
        self.reel = reel
        self.eventType = eventType
        self.notes = []
        self.trackType = 'V'
        self.sourceIn = None
        self.sourceOut = None
        self.recordIn = None
        self.recordOut = None

    def serialize(self, number):
        eventFmt = '{event:03d}    {reel}    {trackType} {editType}     {sourceIn} {sourceOut} {recordIn} {recordOut}'
        event = eventFmt.format(event=number, reel=self.reel, trackType=self.trackType, editType=self.eventType,
                                sourceIn=self.sourceIn, sourceOut=self.sourceOut,
                                recordIn=self.recordIn, recordOut=self.recordOut)
        lines = [event]
        lines.extend(['* ' + x for x in self.notes])
        return NEW_LINE.join(lines) + NEW_LINE

class EDL(object):
    def __init__(self, title):
        super(EDL, self).__init__()
        self._events = []
        self.title = title

    def addCut(self, clip, clipStart, clipEnd, timeLineStart, timeLineEnd):
        event = Event('EdlReel', eventType='C')
        event.sourceIn = clipStart
        event.sourceOut = clipEnd
        event.recordIn = timeLineStart
        event.recordOut = timeLineEnd
        event.notes = [
            'FROM CLIP NAME: ' + clip.name
        ]
        self._events.append(event)

    def write(self, f):
        """
        Takes a file pointer to write out the contents of this EDL.
        :param f:
        :return:
        """
        f.write('TITLE: %s' % self.title)
        f.write(NEW_LINE)
        f.write('FCM: NON-DROP FRAME')
        f.write(NEW_LINE)
        f.write(NEW_LINE)

        for i, event in enumerate(self._events):
            f.write(event.serialize(i))
            f.write(NEW_LINE)


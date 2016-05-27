"""
A tool which generates an EDL file from some kind of input.

Usage:
  cli.py cache <audio_file> <output_beat_cache>
  cli.py generate <beat_cache> <muse_eeg_csv> <clip_description> <output_edl>
  cli.py graph <muse_eeg_csv>
  cli.py (-h | --help)

Options:
  -h --help             Show this screen.

"""

from docopt import docopt
from zoic_api.logger import LOG
from pprint import pformat, pprint
from edllib import EDL, Clip, TimeCode
import random
import json
import os
import datetime
import time
import csv
import numpy
import math

__author__ = 'bjarrett'

FRAME_RATE = 24/1.001


class MoodyClip(Clip):
    def __init__(self, name):
        super(MoodyClip, self).__init__(name)
        self.concentrate = 0
        self.mellow = 0
        self.tags = set()
        self.lastUsedEnd = None

def convertTimeStamp(ts):
    dt = datetime.datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
    return time.mktime(dt.timetuple())

def readEegData(eegPath):
    headers = []
    rows = []
    with open(eegPath, 'rb') as f:
        reader = csv.reader(f)

        firstTimeStamp = None
        for i, row in enumerate(reader):
            if i == 0:
                headers = [x.strip() for x in row]
                continue

            d = dict([(header, value) for header, value in zip(headers, row)])
            d['TimeStamp'] = convertTimeStamp(d['TimeStamp'])

            if firstTimeStamp is None:
                firstTimeStamp = d['TimeStamp']
                d['Seconds'] = 0
            else:
                d['Seconds'] = d['TimeStamp'] - firstTimeStamp

            for k in d.keys():
                if k in ('TimeStamp', 'Seconds'):
                    continue
                v = d[k]
                if v.strip() == '':
                    v = None
                else:
                    v = float(v)
                d[k] = v
            rows.append(d)

    seconds = numpy.array([x['Seconds'] for x in rows])
    mellow = numpy.array([x['Mellow'] for x in rows])
    concentration = numpy.array([x['Concentration'] for x in rows])
    return seconds, mellow, concentration

def readEmotionData(filepath, metrics):
    headers = []
    rows = []
    with open(filepath, 'rb') as f:
        reader = csv.reader(f)

        firstTimeStamp = None
        for i, row in enumerate(reader):
            if i == 0:
                headers = [x.strip() for x in row]
                continue

            d = dict([(header, value) for header, value in zip(headers, row)])

            if firstTimeStamp is None:
                firstTimeStamp = d['timestamp'] / 1000
                d['Seconds'] = 0
            else:
                d['Seconds'] = d['timestamp'] / 1000 - firstTimeStamp

            for k in d.keys():
                if k in ('timestamp', 'Seconds'):
                    continue
                v = d[k]
                if v.strip() == '':
                    v = None
                else:
                    v = float(v)
                d[k] = v
            rows.append(d)

    seconds = numpy.array([x['Seconds'] for x in rows])

    metricsDict = dict()
    for metric in metrics:
        metricsDict[metric] = numpy.array([x[metric + 'ct_emotion_nonlinear_causal'] for x in rows])

    return seconds, metricsDict

def saveAudioCache(audioPath, cachePath):
    import librosa
    y, sr = librosa.load(audioPath, sr=None)
    y_harmonic, y_percussive = librosa.effects.hpss(y)
    tempo, beats = librosa.beat.beat_track(y=y_percussive, sr=sr)
    beatTimes = librosa.frames_to_time(beats, sr=sr)

    beatTimes = list(beatTimes)
    with open(cachePath, 'wb') as f:
        json.dump(beatTimes, f, indent=4)

def loadAudioCache(cachePath):
    with open(cachePath, 'rb') as f:
        return json.load(f)

def chooseClip(targetMellow, targetConcentrate, targetEmotions, targetValence, clips, lastClip, reusedCounter):
    """
    Determines ideal camera angle and shot content based on source data:
    1) Sums all targetEmotions to compute emotional intensity of shot as deviation from neutral camera angle (MS-MWS)
    2) Compares targetMellow vs targetConcentrate to choose which direction to select on camera angle spectrum (XCU-CU-MS-MWS-WS-XWS)
    3) OPTION: We can implement targetValence as control over frames per second (slow motion)
    4) TODO: Integrate Watson JSON data to incorporate lyrical emotional data
    """
    # Control randomness factor in choosing clip for iteration (0 = no randomness, 1.0 = highly random)
    randomness = 1.0

    def score(target, value):
        scoreDiff = target - value
        if scoreDiff == 0:
            # Cannot divide by zero
            scoreDiff = 0.01
        return 1. / scoreDiff

    # Compute the score for each and then pick the highest score.
    scores = []
    for clip in clips:
        trackScores = []
        for metric in metrics:
            trackScores.append(score(metric, clip[metric])
        averageScore = numpy.mean(trackScores)
        if clip == lastClip:
            averageScore = averageScore * (1 / (math.log(reusedCounter + 1) + 1))
        if randomness > 0:
            averageScore = averageScore + randomnessFactor * numpy.random.uniform(-1 * averageScore, averageScore)
        scores.append(
            (clip, averageScore)
        )

    sortedByScores = sorted(scores, key=lambda x: x[1], reverse=True)
    return sortedByScores[0][0]

def generateEdl(beatCachePath, clipDescriptionPath, musePath, affdexPath, outputPath):
    beats = loadAudioCache(beatCachePath)
    if len(beats) <= 0:
        raise ValueError('There are no beats!')

    # Load up the clip description.
    f = open(clipDescriptionPath, 'rb')
    clipDescriptionBlob = json.load(f)
    f.close()

    # Get our clip objects.
    clips = []
    for clip, clipInfo in clipDescriptionBlob['clips'].iteritems():
        c = MoodyClip(clip)
        c.startTc = TimeCode.fromString(clipInfo['start_tc'], frameRate=FRAME_RATE)
        c.duration = clipInfo['duration']
        c.concentrate = clipInfo['concentrate']
        c.mellow = clipInfo['mellow']
        clips.append(c)

    emotionMetrics = ['joy', 'disgust', 'sadness', 'anger', 'surprise', 'contempt', 'fear', 'valence']

    # Read key data points
    eeg = readEegData(musePath)
    emotions = readEmotionData(affdexPath, emotionMetrics)
    edlFile = EDL(os.path.splitext(os.path.basename(outputPath))[0])

    createCuts(scenes=clipDescriptionBlob['scenes'], clips=clips, eeg=eeg, emotions=emotions, beats=beats, edl=edlFile)

    with open(outputPath, 'wb') as f:
        edlFile.write(f)

def createCuts(scenes, clips, eeg, emotions, beats, edl):
    """

    :param scenes: A list of dicts representing the allowed clips for a duration
    :param clips: a list of Clip objects
    :param eeg: a list of dicts for each eeg frame.
    :param emotions: a list of dicts for each emotion frame.
    :param beats: a list of floating point seconds for each beat time
    :param edl: the EDL object to write cuts to.
    :return:
    """

    seconds, mellow, concentration = eeg
    emotionTime, emotionData = emotions
    emotionSampleRate = 14  # samples per second

    slateFrames = 20
    firstTime = 0
    lastClip = None
    lastCut = 1

    sameClipBeatLimit = 20
    sameClipBeatCounter = 0

    for beatTime in beats:
        # Time in seconds.
        # Find the averages for this beat section.
        first = firstTime
        last = int(round(beatTime))

        mellowSegment = mellow[first:last + 1]
        # The amount of mellow for this beat section
        mellowAvg = numpy.mean(mellowSegment)

        concentrateSegment = concentration[first:last + 1]
        # The amount of concentration for this beat section
        concentrateAvg = numpy.mean(concentrateSegment)

        # The averages of each emotion in this segment
        emotionAverages = {}
        for emotion in emotionData:
            emotionSegment = emotion[first*emotionSampleRate:last*emotionSampleRate + emotionSampleRate]
            emotionAvg = numpy.mean(emotionSegment)
            # Separate valence from dictionary to use as separate metric control
            if emotion != 'valence':
                emotionAverages[emotion] = emotionAvg
            else:
                valenceAvg = emotionAvg

        # What clips are we choosing from in this beat segment?
        chosenScene = None
        sceneStartT = 0
        for scene in scenes:
            endTime = TimeCode.fromString(scene['end_time'], frameRate=FRAME_RATE).toSeconds()
            if beatTime > sceneStartT and beatTime < endTime:
                chosenScene = scene
                break
            sceneStartT = endTime

        clipsByName = dict([(x.name, x) for x in clips])
        clipSelection = [clipsByName[x] for x in chosenScene['clips']]

        skipToNextBeat = False
        while True:
            clip = chooseClip(mellowAvg, concentrateAvg, emotionAverages, valenceAvg, clipSelection, lastClip, sameClipBeatCounter)
            print clip, first, last
            if clip == lastClip:
                if sameClipBeatCounter > sameClipBeatLimit:
                    clipSelection.remove(clip)
                    continue
                skipToNextBeat = True
                break

            beatFrame = beatTime * FRAME_RATE

            if clip.lastUsedEnd is not None:
                clipStart = clip.lastUsedEnd
            else:
                clipStart = TimeCode.fromFrame(clip.startTc.toFrames() + slateFrames, frameRate=FRAME_RATE)
                print 'clipStart = ' + str(clipStart)
            # Length in frames.
            length = beatFrame - lastCut
            clipEndFrame = clipStart.toFrames() + length
            # Check if this is past the end of the clip. If it is we have to choose another one.
            clipsActualEndFrame = clip.startTc.toFrames() + clip.duration
            if clipEndFrame > clipsActualEndFrame:
                # We must chose another one. There isn't enough clip here!
                print 'clip isn\'t long enough!'
                clipSelection.remove(clip)
                if len(clipSelection) == 0:
                    raise ValueError('Uh oh, no possible clips for this cut.')
                continue

            clipEnd = TimeCode.fromFrame(clipEndFrame, frameRate=FRAME_RATE)
            clip.lastUsedEnd = clipEnd
            break

        if skipToNextBeat:
            sameClipBeatCounter += 1
            continue
        sameClipBeatCounter = 0

        print 'cut!', clip
        edl.addCut(clip,
                 clipStart=clipStart,
                 clipEnd=clipEnd,
                 timeLineStart=TimeCode.fromFrame(lastCut, frameRate=FRAME_RATE),
                 timeLineEnd=TimeCode.fromFrame(beatFrame, frameRate=FRAME_RATE))
        lastCut = beatFrame

        firstTime = last
        lastClip = clip


def main():
    arguments = docopt(__doc__)
    LOG.debug('Arguments:\n%s', pformat(arguments))

    if arguments['cache']:
        audioPath = arguments['<audio_file>']
        if not os.path.exists(audioPath):
            raise ValueError('Audio file does not exist')
        cachePath = arguments['<output_beat_cache>']
        return saveAudioCache(audioPath, cachePath)

    if arguments['generate']:
        beatCachePath = arguments['<beat_cache>']
        if not os.path.exists(beatCachePath):
            raise ValueError('Beat cache file does not exist')
        clipDescriptionPath = arguments['<clip_description>']
        if not os.path.exists(clipDescriptionPath):
            raise ValueError('Clip description does not exist.')
        musePath = arguments['<muse_eeg_csv>']
        if not os.path.exists(musePath):
            raise ValueError('EEG Path does not exist.')
        affdexPath = arguments['<emotion_csv>']
        if not os.path.exists(affdexPath):
            raise ValueError('Emotion Path does not exist.')
        outputEdlPath = arguments['<output_edl>']
        return generateEdl(beatCachePath=beatCachePath,
                           clipDescriptionPath=clipDescriptionPath,
                           musePath=musePath,
                           affdexPath=affdexPath,
                           outputPath=outputEdlPath)

    if arguments['graph']:
        from matplotlib import pyplot as plt

        musePath = arguments['<muse_eeg_csv>']
        if not os.path.exists(musePath):
            raise ValueError('Muse does not exist.')
        seconds, mellow, concentration = readEegData(musePath)
        plt.plot(seconds, mellow, 'y', label='Mellow')
        plt.plot(seconds, concentration, 'b', label='Concentration')
        plt.legend()
        plt.xlabel('Seconds')
        plt.ylabel('Amount')
        plt.show()

if __name__ == '__main__':
    main()

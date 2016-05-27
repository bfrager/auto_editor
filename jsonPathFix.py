import sys
import os
import numpy
from pprint import pprint

#tags lookup dict {'<clipname_search_string>':'<tag>'}
tags = {
    'girl': 'girl',
    'guy': 'guy',
    'sun': 'sun',
    'moon': 'moon',
    '_cu': 'cu',
    '_med': 'ms',
    '_full': 'fs',
    '_wide': 'ws',
    '_superwide': 'xws',
    '_high': 'overhead',
    '_pov': 'pov'
    }

#section breakdown (to match with Q:\Comm\tai\vault\ShotBreakdown\tai_shot_breakdown_v1.xlsx)
scene_ids = {
    1:{"label": "intro", "end_time": "00:00:00:50"},
    2:{"label": "girlSingGuyBeginRun", "end_time": "00:00:59:00"},
    2.1:{"label": "sunset_moonset", "end_time": "00:01:14:00"},
    3:{"label": "girlSingGuyRunOut", "end_time": "00:01:52:00"},
    3.1:{"label": "girlBeginRunGuyRunOut", "end_time": "00:02:06:00"},
    3.2:{"label": "girlRunOutGuyRunOut", "end_time": "00:02:18:00"},
    4:{"label": "girlStopGuyStop", "end_time": "00:02:50:00"},
    5:{"label": "girlRunBackGuyRunBack", "end_time": "00:03:36:00"},
    6:{"label": "girlGuyTogether", "end_time": "00:03:56:00"}
    }

JSON_DATA = """
{
  "clips": {
<clipLine>
  },
  "scenes": [
<scene>
  ]
}
"""

CLIP_LINE = '    "<fileName>": {"scene_id": <scene_id>, "mellow": <mellow>, "concentrate": <concentrate>, "tags":[<tags>], "start_tc":"00:00:00:00", "duration":109},'
SCENE_LINE = '        "<fileName>",'
SCENE_JSON = """
{
  "scene_id": <scene_id>,
  "label": <label>,
  "end_time": <end_time>,
  "clips": [
<sceneLine>
]
},

"""

DRONE_MOVS = r'Q:\Comm\tai\vault\HoudiniShotgunPrevis'

NON_DRONE_MOVS = [
	r'Q:\Comm\tai\tai100\3D\movies\tai100_100_000_girl_intro_pre_001.mov',
	r'Q:\Comm\tai\tai100\3D\movies\tai100_100_000_guy_intro_pre_001.mov',
	r'Q:\Comm\tai\tai100\3D\movies\tai100_100_000_girl_sing_pre_001.mov',
	r'Q:\Comm\tai\tai100\3D\movies\tai100_100_000_girl_stop_turn_pre_001.mov',
	r'Q:\Comm\tai\tai100\3D\movies\tai100_100_000_guy_stop_turn_pre_001.mov',
	r'Q:\Comm\tai\tai100\3D\movies\tai100_100_000_sunset_pre_001.mov',
	r'Q:\Comm\tai\tai100\3D\movies\tai100_100_000_moonset_pre_001.mov',
	r'Q:\Comm\tai\tai100\3D\movies\tai100_100_000_eclipse_pre_001.mov',
]

def main(script):
	newJson = JSON_DATA
	fileList = []
	droneList = os.listdir(DRONE_MOVS)
	droneList.sort()
	fileList.extend(droneList)

	for nonDrone in NON_DRONE_MOVS:
		fileList.append(nonDrone.split('\\')[-1])

	clipData = []
    # sceneData = []

	for fileName in fileList:
		clipData.append(CLIP_LINE.replace('<fileName>', fileName).replace('<tags>', addTags(fileName)).replace('<mellow>', numpy.random.uniform(0,1)).replace('<concentrate>', numpy.random.uniform(0,1)))

    for scene in scene_ids:

        ##TODO: create dict out of clipData JSON object to search for scene_id in clip
    	# sceneLines = []
        # for fileName in fileList:
        #     if scene == filename['scene_id']:
        #         sceneLines.append(SCENE_LINE.replace('<fileName>', fileName))

        sceneData.append(SCENE_JSON.replace('<scene_id>', scene).replace('<label>', scene['label']).replace('<end_time>', scene['end_time']))
        #TODO: add one more replace to sceneData: .replace('<sceneLine>', '\n'.join(sceneLines)

	newJson = newJson.replace('<clipLine>', '\n'.join(clipData)).replace('<scene>', '\n'.join(sceneData))
	print newJson

def addTags(clipName)
    clipTags = []
    for tag in tags:
        if tag in clipName:
            clipTags.append(tags[tag])
    clipTagsFormatted = ', '.join(clipTags)
    clipTagsFormatted.rstrip(', ')
    return clipTagsFormatted

if __name__ == '__main__':
	main(*sys.argv)

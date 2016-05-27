__author__ = 'bjarrett'


import hiero.core

myProject = hiero.core.projects()[-1]
clipsBin = myProject.clipsBin()

clipNames = []

for i in clipsBin.items(hiero.core.Bin.ItemType.kBin):
    for binItem in i.items():
        clip = binItem.activeItem()
        media = clip.mediaSource()
        meta = media.metadata()
        name = meta['foundry.source.filename']
        start = meta['foundry.source.startTC']
        duration = meta['foundry.source.duration']
        clipNames.append((name, start, duration))

clipNames.sort(key=lambda x: x[0])
for clip in clipNames:
    print clip
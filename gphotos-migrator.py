#
# Description of project
# Identify any missing images in nextcloud folder vs google photos
#

import hashlib, os, re, exiftool, shutil, sys
from typing import Counter
from progress.bar import Bar

def generateHash(filePath):
    with open(filePath, 'rb') as f:
        fileHash = hashlib.md5()
        while chunk := f.read(8192):
            fileHash.update(chunk)
    return fileHash.hexdigest()

def newPaths(list):
    for i in range(len(list)):
        metadata = list[i]['attributes']

        if 'EXIF:DateTimeOriginal' in metadata.keys():
            key = 'EXIF:DateTimeOriginal'
        elif 'QuickTime:CreateDate' in metadata.keys():
            key = 'QuickTime:CreateDate'
        year = metadata[key][0:4]
        month = metadata[key][5:7]
        day = metadata[key][8:10]
        hour = metadata[key][11:13]
        min = metadata[key][14:16]
        sec = metadata[key][17:19]
        newPath = f"{dstPath}/{year}/{month}/{year}-{month}-{day}_{hour}{min}{sec}_{list[i]['name']}"
        list[i].update({
            'newPath': newPath
            })

def processFiles(list):
    bar = Bar('Processing', max=len(list))
    for i in range(len(list)):
        hash = generateHash(list[i]['path'])
        with exiftool.ExifTool() as et:
            metadata = et.get_tags([
                'File:FileName',
                'GPS:GPSLatitudeRef',
                'GPS:GPSLatitude',
                'GPS:GPSLongitudeRef',
                'GPS:GPSLongitude',
                'GPS:GPSAltitudeRef',
                'GPS:GPSAltitude',
                'EXIF:DateTimeOriginal',
                'EXIF:CreateDate',
                'EXIF:ModifyDate',
                'QuickTime:CreateDate'
                ], list[i]['path'])
        metadata.pop('SourceFile')
        data = {
            'attributes': {
                'md5': hash
            }
        }
        data['attributes'].update(metadata)
        list[i].update(data)
        bar.next()
    bar.finish()
    #return list

def findFiles(path):
    rePattern = re.compile('(.json)$')
    listOfFiles = []
    counter = 0
    print(f"Gathering files for path: {path}")
    for root, subdirs, files in os.walk(path):
        for file in files:
            if rePattern.search(file) is None:
                counter += 1
                print(f"Found {counter} files", end="\r")
                filePath = os.path.join(root, file)
                listOfFiles.append({
                    'name': file,
                    'path': filePath
                })
    print("")
    return listOfFiles

if __name__ == "__main__":

    args = sys.argv[1:]

    if len(args) == 2 and os.path.exists(args[0]) and os.path.exists(args[1]):

        srcPath = args[0]
        dstPath = args[1]

        # Generate list of dict of each file for google photos library (source library) and
        # nextcloud photo library (destination library)
        srcFiles = findFiles(srcPath)
        dstFiles = findFiles(dstPath)

        # FOR TESTING ############
        #srcFiles = srcFiles[:10]
        #dstFiles = dstFiles[:10]
        ##########################

        print(f"Processing files in source directory")
        processFiles(srcFiles)

        print(f"Processing files in destination directory")
        #print(dstFiles[21]) <- problem file with no Date Time Original tag
        processFiles(dstFiles)

        # dstAttributes = [item['attributes'] for item in dstFiles]
        # filesWithDifferences = [d for d in srcFiles if d['attributes'] not in dstAttributes]

        # Files to copy
        dstHashes = [item['attributes']['md5'] for item in dstFiles]
        filesToCopy = [f for f in srcFiles if f['attributes']['md5'] not in dstHashes]

        #test

        # Files to overwrite
        filesToOverwrite = []
        for i in range(len(srcFiles)):
            for j in range(len(dstFiles)):
                if srcFiles[i]['attributes']['md5'] == dstFiles[j]['attributes']['md5']:
                    if srcFiles[i]['attributes'] != dstFiles[j]['attributes']:
                        file = {
                            'name': srcFiles[i]['name'],
                            'srcPath': srcFiles[i]['path'],
                            'dstPath': dstFiles[j]['path']
                        }
                        file.update(srcFiles[i]['attributes'])
                        filesToOverwrite.append(file)

        print(filesToOverwrite)

        #delta = [i for i in filesWithDifferences if i not in filesToCopy] + [j for j in filesToCopy if j not in filesWithDifferences]

        print('Summary of files')
        print(f"Total files to copy: {len(filesToCopy)}")
        print(f"Total files to overwrite: {len(filesToOverwrite)}")

    elif len(args) > 2:
        print('Please only enter 2 arguments')
    elif (not os.path.exists(args[0])) or (not os.path.exists(args[1])):
        print('Please use real paths')
    else:
        print('Too few arguments')
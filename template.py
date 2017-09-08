#!/usr/bin/env python3

import os, io, sys, fileinput, glob, zipfile, re, ntpath, shutil, uuid, tempfile, lzma, json

def gettempdir():
    #return str(uuid.uuid1())
    return os.path.join(tempfile.gettempdir(), str(uuid.uuid1()))

def is_subdir(path, directory):
    path = os.path.realpath(path)
    directory = os.path.realpath(directory)
    relative = os.path.relpath(path, directory)
    return not relative.startswith(os.pardir + os.sep)

def get_files(dir, ext):
    result = []
    #print(dir)
    for root, dirs, files in os.walk(dir):
        for file in files:
            if file.endswith("." + ext):
                result.append(os.path.join(root, file))
        for directory in dirs:
            result.extend(get_files(directory, ext))
    return result

def find_guids_in_file(fileName):
    guids = dict({})
    regex = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}", re.I)
    with open(fileName) as f:
        content = f.readlines()
    content = [x.strip() for x in content] 

    for entry in content:
        match = regex.search(entry)
        if match:
            guids[match.string[match.start():match.end()]] = str(uuid.uuid1())
    return guids

def find_guids(files):
    guids = dict({})
    for fileName in files:
        guids = {**guids, **find_guids_in_file(fileName)} 
    return guids

def replace_in_file(fileName, entry, replace):
    with fileinput.FileInput(fileName, inplace=True) as file:
        for line in file:
            print(line.replace(entry, replace), end='')

def replace_in_files(files, entry, replace):
    for fileName in files:
        replace_in_file(fileName, entry, replace)

def replace_by_dict(files, dictionary):
    for key, value in dictionary.items():
        replace_in_files(files, key, value)

def replace_by_dict_in_file(fileName, dictionary):
    for key, value in dictionary.items():
        replace_in_file(fileName, key, value)

def process_project_files(project, project_dir):
    files = get_files(project_dir, "vcxproj")

def collect_files(dir, exts):
    files = []
    for ext in exts:
        files += get_files(dir, ext)
    return files

def process_source_files(dir):
    return collect_files(dir, ["c", "cpp", "cxx", "h", "hpp", "hxx", "vcxproj"])

def select_filename(filename, template_name):
    basename = ntpath.basename(filename)
    splitted_name = os.path.splitext(basename)
    clear_name = splitted_name[0]
    if clear_name == template_name:
        return "$project$" + splitted_name[1]
    else:
        return basename

def pack_template(solutionDir, sourceDir, name):
    zipName = name + ".project.zip"
    files = process_source_files(sourceDir)
    with zipfile.ZipFile(zipName, 'w') as packed:
        for file in files:
            packed.write(file, os.path.relpath(file, solutionDir))
    return zipName

def unpack_template(zipName, targetDir):
    with zipfile.ZipFile(zipName) as packed:
        packed.extract(file, targetDir)

def read_file(name):
    file = open(name.replace("\\", "/"), 'r')
    data = file.read().replace("\r\n", "\n")
    return data

def clean_path(path):
    path = path.replace('/',os.sep).replace('\\',os.sep)
    if os.sep == '\\' and '\\\\?\\' not in path:
        # fix for Windows 260 char limit
        relative_levels = len([directory for directory in path.split(os.sep) if directory == '..'])
        cwd = [directory for directory in os.getcwd().split(os.sep)] if ':' not in path else []
        path = '\\\\?\\' + os.sep.join(cwd[:len(cwd)-relative_levels]\
                         + [directory for directory in path.split(os.sep) if directory!=''][relative_levels:])
    return path

def get_projects_info_from_sln(fileName):
    basepath = ntpath.dirname(os.path.abspath(fileName))
    content = read_file(fileName)
    p = re.compile('Project\("\{8BC9CEB8-8B4A-11D0-8D11-00A0C91BC942\}"\)(.*?)EndProject\n', re.MULTILINE | re.DOTALL)
    projects = {}
    for entries in p.findall(content):
        p = re.compile('"(.*?)"');
        projectName = p.findall(entries)

        #check for "real" project
        if len(projectName) != 3:
            continue
        
        # extract dependencies
        p = re.compile('\} = \{([A-F0-9\-]{0,})\}')
        dependencies = p.findall(entries)
        
        # identify the absolute path for the project file    
        projectFilename = ntpath.abspath(ntpath.join(basepath, projectName[1]))
               
        # remove { } from the ID
        id = projectName[2][1:-1]
        projects[id] = {
            'id' : id,
            'name' : projectName[0],
            'projectFilename' : projectFilename,
            'dependencies' : dependencies
        }
    return projects

def pack_sln(solutionFileName):
    solutionDir = ntpath.dirname(solutionFileName)
    #print(os.path.abspath(solutionDir))
    zipName = os.path.splitext(ntpath.basename(solutionFileName))[0] + ".zip"
    schemeName = os.path.splitext(solutionFileName)[0] + ".json"
    with open(schemeName) as f:
        metadata = json.load(f)
    
    with zipfile.ZipFile(zipName, 'w') as packed:
        packed.write(solutionFileName, "$solution$.sln", compress_type = zipfile.ZIP_LZMA)
        packed.write(schemeName, "$scheme$.json", compress_type = zipfile.ZIP_LZMA)        
        for key, item in get_projects_info_from_sln(solutionFileName).items():
            projectName = item['name']
            projectFileName = item['projectFilename']
            projectDir = ntpath.dirname(projectFileName)
            #print(projectDir)
            if is_subdir(projectDir, solutionDir):
                projectZipName = pack_template(solutionDir, os.path.join(solutionDir, projectDir), projectName)
                packed.write(projectZipName, compress_type = zipfile.ZIP_LZMA)
                os.remove(projectZipName)
            pass
    #print("solution template: ", zipName, " is ready")

def moveResult(sourceDir, outDirs, targetDir):
    for directory in outDirs:
        source = sourceDir + "\\" + directory
        target = targetDir + "\\" + directory
        if os.path.exists(target):
            try:
                shutil.rmtree(target)
            except NotADirectoryError:
                try:
                    os.unlink(target)
                except FileNotFoundError:
                    pass
        shutil.move(source, target)

    for filename in os.listdir(sourceDir):
        target = os.path.join(targetDir, filename)
        if not os.path.isdir(sourceDir + "\\" + filename):
            if os.path.exists(target):
                try:
                    shutil.rmtree(target)
                except NotADirectoryError:
                    try:
                        os.unlink(target)
                    except FileNotFoundError:
                        pass
            shutil.move(os.path.join(sourceDir, filename), targetDir)

def extractReplaceDict(zipName, extractDir, newName):
    nameReplaceDict = dict()
    with zipfile.ZipFile(zipName, 'r') as packed:
        packed.extractall(extractDir)
        schemeName = extractDir + "/$scheme$.json"
        with open(schemeName) as f:
            metadata = json.load(f)
            for key, item in metadata.items():
                if item == "rename": 
                    nameReplaceDict[key] = newName
                elif item == "prefix": 
                    nameReplaceDict[key] = newName + key
                else:
                    nameReplaceDict[key] = key;
    return nameReplaceDict

def replaceFilenamesByDict(resultDir, nameReplaceDict):
    outDirs = list()
    for root, dirs, files in os.walk(resultDir):
        for directory in dirs:
            if (directory in nameReplaceDict):
                srcDirName = root + "\\" + directory
                dstDirName = root + "\\" + nameReplaceDict[directory]
                shutil.move(srcDirName, dstDirName)
                outDirs += {dstDirName[len(resultDir) + 1:]}

    for fileName in process_source_files(resultDir):
        baseName = ntpath.basename(fileName)
        splitted = os.path.splitext(baseName)
        nakedName = splitted[0]
        ext = splitted[1]
        if nakedName in nameReplaceDict:
            resultFileName = os.path.split(fileName)[0] + "\\" + nameReplaceDict[nakedName] + ext
            os.rename(fileName, resultFileName)
    return outDirs

def extractArchive(zipName, extractDir, resultDir, projectsFilter):
    for fileName in get_files(extractDir, "zip"):
        with zipfile.ZipFile(fileName, 'r') as packed:
            splitted_name = os.path.splitext(os.path.splitext(ntpath.basename(fileName))[0])
            if splitted_name[0] in projectsFilter or len(projectsFilter) == 0:
                packed.extractall(resultDir)

def unpack_solution(zipName, moduleDir, newSolutionName):
    extractDir = gettempdir()
    resultDir = gettempdir()

    nameReplaceDict = extractReplaceDict(zipName, extractDir, newSolutionName)
    extractArchive(zipName, extractDir, resultDir, set())
    shutil.copy(ntpath.join(extractDir, "$solution$.sln"), ntpath.join(resultDir, newSolutionName + ".sln"))

    projfiles = collect_files(resultDir, ["c", "cpp", "cxx", "h", "hpp", "hxx", "sln", "vcxproj"])
    uids = {**nameReplaceDict, **find_guids(get_files(resultDir, "vcxproj"))}
    replace_by_dict(projfiles, uids)
    moveResult(resultDir, replaceFilenamesByDict(resultDir, nameReplaceDict), moduleDir)
    shutil.rmtree(extractDir)

def unpack_project(zipName, moduleDir, projectSource, projectTarget):
    extractDir = gettempdir()
    resultDir = gettempdir()

    nameReplaceDict = extractReplaceDict(zipName, extractDir, projectTarget)
    extractArchive(zipName, extractDir, resultDir, set({projectSource}))
    
    projfiles = collect_files(resultDir, ["c", "cpp", "cxx", "h", "hpp", "hxx", "vcxproj"])
    uids = {**nameReplaceDict, **find_guids(get_files(resultDir, "vcxproj"))}
    replace_by_dict(projfiles, uids)
    moveResult(resultDir, replaceFilenamesByDict(resultDir, nameReplaceDict), moduleDir)
    shutil.rmtree(extractDir)

#pack_sln("WizardTemplates/_static_library.sln")
#unpack_solution("_static_library.zip", "NewModule", "FSM")
#unpack_project("_static_library.zip", "NewModule", "staticLibrary", "StaticTest")

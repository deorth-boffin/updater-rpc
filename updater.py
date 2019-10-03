#!/usr/bin/python3
from utils import *
from appveyor import *
import json
import shutil
from distutils import dir_util
from copy import deepcopy




class Updater:
    CONF = {
    "basic":{},
    "build":
    {    
        "branch": None,
        "no_pull": False
    },
    "download":
    {
        "keyword": "",
        "exclude_keyword": "/",
        "filetype": "7z"
    },
    "process":
    {
        "allow_restart": False
    },
    "decompress":
    {
    "include_file_type": [],
    "exclude_file_type": [],
    "single_dir": True,
    "keep_download_file": True
    }
    }
    
    aria2=Aria2Rpc(ip="127.0.0.1", port="6800", passwd="")
    @classmethod
    def setAria2Rpc(cls, ip="127.0.0.1", port="6800", passwd=""):
        cls.aria2=Aria2Rpc(ip,port,passwd)




    def __init__(self, name, path):
        self.path = path
        self.name = name

        self.conf = deepcopy(self.CONF)
        self.newconf = LoadConfig("config/%s.json"%name).config
        
        for group in self.newconf:
            self.conf[group].update(self.newconf[group])

        try:
            self.conf["process"]["image_name"]
        except KeyError:
            self.conf["process"].update({"image_name": self.name+".exe"})

        if self.conf["basic"]["api_type"] == "github":
            self.api = GithubApi(
                self.conf["basic"]["account_name"], self.conf["basic"]["project_name"])
        elif self.conf["basic"]["api_type"] == "appveyor":
            self.api = AppveyorApi(
                self.conf["basic"]["account_name"], self.conf["basic"]["project_name"], self.conf["build"]["branch"])

        self.dlurl = self.api.getDlUrl(
            self.conf["download"]["keyword"], self.conf["download"]["exclude_keyword"], self.conf["download"]["filetype"], self.conf["build"]["no_pull"])
        try:
            self.filename = os.path.basename(self.dlurl)
        except TypeError:
            raise ValueError("Can't get download url!")

    def checkIfUpdateIsNeed(self):
        versionfile=self.name+".VERSION"
        self.version = self.api.getVersion()
        self.versionfile_path = os.path.join(self.path, versionfile)
        try:
            self.versionfile = open(self.versionfile_path, 'r')
            self.oldversion = self.versionfile.read()
            self.versionfile.close()
        except:
            self.oldversion = ""

        return not self.version == self.oldversion

    def download(self):
        self.dldir = os.path.join(self.path, "downloads")
        if not os.path.exists(self.dldir):
            os.makedirs(self.dldir)
        self.aria2.wget(self.dlurl, self.dldir)

    def extract(self):
        self.fullfilename = os.path.join(self.dldir, self.filename)
        f = Py7z(self.fullfilename)
        filelist0 = f.getFileList()
        if self.conf["decompress"]["include_file_type"] == [] and self.conf["decompress"]["exclude_file_type"] == []:
            f.extractAll(self.path)
        else:
            if self.conf["decompress"]["include_file_type"] != []:
                filelist1 = []
                for file in filelist0:
                    for include in self.conf["decompress"]["include_file_type"]:
                        if file.split(r".")[-1] == include:
                            filelist1.append(file)
            else:
                filelist1 = list(filelist0)
            filelist0 = []
            for file in filelist1:
                flag = False
                for exclude in self.conf["decompress"]["exclude_file_type"]:
                    type0 = file.split(r".")[-1]
                    if type0 == exclude:
                        flag = True
                if not flag:
                    filelist0.append(file)
            f.extractFiles(filelist0, self.path)
        prefix = f.getPrefixDir()
        if self.conf["decompress"]["single_dir"] and prefix != "":
            for file in os.listdir(os.path.join(self.path, prefix)):
                new = os.path.join(self.path, prefix, file)
                try:
                    shutil.copy(new, self.path)
                except (IsADirectoryError, PermissionError):
                    old = os.path.join(self.path, file)
                    dir_util.copy_tree(new, old)
            shutil.rmtree(os.path.join(self.path, prefix))
        if not self.conf["decompress"]["keep_download_file"]:
            os.remove(self.fullfilename)

    def updateVersionfile(self):
        with open(self.versionfile_path, 'w') as self.versionfile:
            self.versionfile.write(self.version)
        self.versionfile.close()

    def run(self, force=False):
        if self.checkIfUpdateIsNeed() or force:
            self.download()
            self.proc = ProcessCtrl(self.conf["process"]["image_name"])
            if self.conf["process"]["allow_restart"]:
                self.proc.stopProc()
                self.extract()
                self.proc.startProc()

            else:
                while self.proc.checkProc():
                    print("请先关闭正在运行的"+self.name, end="\r")
                    time.sleep(1)
                self.extract()
            self.updateVersionfile()
        else:
            # TODO:Use log instead of print
            print("当前%s已是最新，无需更新！" % (self.name))


if __name__ == "__main__":
    # update=Updater("pd_loader","/root/pdaft")
    # update=Updater(sys.argv[1],sys.argv[2])
    # update.run()
    if sys.platform == "win32":
        citra_path = r"D:\citra"
        rpcs3_path = r"D:\rpcs3"
        pd_loader_path = r"E:\Hatsune Miku Project DIVA Arcade Future Tone"
        ds4_path = r"D:\Program Files\DS4Windows"
    else:
        citra_path = "/root/citra"
        rpcs3_path = "/root/rpcs3"
        pd_loader_path = "/root/pdaft"
        ds4_path = "/root/ds4"

    moon=Updater("moonlight_win", "foo")
    
    ds4 = Updater("ds4windows", ds4_path)
    ds4.run()
    

    citra = Updater("citra", citra_path)
    citra.run()
    
    rpcs3 = Updater("rpcs3_win", rpcs3_path)
    rpcs3.run()
    
    pdl = Updater("pd_loader", pd_loader_path)
    pdl.run()
 

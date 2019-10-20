#!/usr/bin/python3
import requests
import re
import os
from utils import getJson, urljoin


class AppveyorApi:
    apiurl = "https://ci.appveyor.com/api"

    def __init__(self, account_name, project_name, branch=None):
        if branch == None:
            self.branch = ""
        else:
            self.branch = "&branch="+branch
        self.account_name = account_name
        self.project_name = project_name

    def getHistory(self):
        self.historyurl = urljoin(self.apiurl, "projects", self.account_name,
                                  self.project_name, "history?recordsNumber=100"+self.branch)
        self.json = getJson(self.historyurl)
        for build in self.json["builds"]:
            yield build["version"]

    def getDlUrl(self, keyword="", no_keyword="/", filetype="7z", no_pull=False):
        for version in self.getHistory():
            self.version = version
            self.buildurl = urljoin(
                self.apiurl, "projects", self.account_name, self.project_name, "build", self.version)
            self.buildjson = getJson(self.buildurl)
            if no_pull:
                try:
                    self.buildjson['build']['pullRequestId']
                    continue
                except KeyError:
                    pass
            self.jobid = self.buildjson["build"]["jobs"][0]["jobId"]
            self.artifactsurl = urljoin(
                self.apiurl, "buildjobs", self.jobid, "artifacts")
            self.artifactsjson = getJson(self.artifactsurl)
            if len(self.artifactsjson) == 0:
                continue
            for fileinfo in self.artifactsjson:
                filename = fileinfo["fileName"]
                if keyword in filename and no_keyword not in filename and filename[-len(filetype):] == filetype:
                    self.filename = filename
                    self.dlurl = urljoin(
                        self.apiurl, "buildjobs", self.jobid, "artifacts", self.filename)
                    return self.dlurl

    def getVersion(self):
        try:
            return self.version
        except AttributeError:
            raise AttributeError(
                "You must run getDlUrl first before tried to getVersion")


class GithubApi:
    apiurl = "https://api.github.com/repos"

    def __init__(self, account_name, project_name):
        self.account_name = account_name
        self.project_name = project_name

    def getReleases(self):
        self.releasesurl = urljoin(
            self.apiurl, self.account_name, self.project_name, "releases")
        return getJson(self.releasesurl)

    def getDlUrl(self, keyword="", no_keyword="/", filetype="7z", no_pull=False):
        for release in self.getReleases():
            if release["name"] != None:
                self.version = release["name"]
            else:
                self.version = release["tag_name"]
            if len(release["assets"]) != 0:
                for file in release["assets"]:
                    if keyword in file["name"] and no_keyword not in file["name"] and file["name"][-len(filetype):] == filetype:
                        return file["browser_download_url"]
            elif filetype == "zip":
                return release["zipball_url"]
            elif filetype == "tar.gz":
                return release["tarball_url"]

    def getVersion(self):
        try:
            return self.version
        except AttributeError:
            raise AttributeError(
                "You must run getDlUrl first before tried to getVersion")


if __name__ == "__main__":
    pass

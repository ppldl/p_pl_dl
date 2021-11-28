from time import sleep
import jsbeautifier
import random
import re
import yt_dlp as youtube_dl

import p_pl_dl_common as dl_common

DEBUG = False

sExtractor  = 'pornve'
sArchive    = rf".\\sites\\{sExtractor}\\dl_hist_{sExtractor}.txt"


def run(sUrl, sCookieSource=None, nVideoLimit=None, bDebug=False):
    print(f"Running {sExtractor} extractor for {sUrl}\r\n")

    if sCookieSource is not None:
        dl_common.parseCookieFile(sCookieSource)

    if dl_common.dCookiesParsed is None:
        print("WARNING :: No cookies were provided! Private videos/playlists will fail to download!\r\n")

    # Attempt initial connection
    dl_common.randomizeHeader()
    html = dl_common.session.get(sUrl, headers=dl_common.dHeaders, cookies=dl_common.dCookiesParsed)
    print(f"Initial connection status: {html.status_code}")
    if html.status_code == 403:
        raise ConnectionError(f"403 Forbidden! Please check if cookies are required! Private videos/playlists cannot be accessed without cookies!")
    elif html.status_code != 200:
        raise ConnectionError(f"Initial connection failed : Status {html.status_code}")
    print()
    sleepRandom(1, 3)

    if bDebug:
        # Save HTML content to a text file for debug
        text_file = open("html_content.txt", "w", encoding='utf-8')
        text_file.write(html.text)
        text_file.close()

    page = Page_Pornve(sUrl)
    sleepRandom(3, 5)

    dYdlOptions = dict(dl_common.dYdlOptions)
    dYdlOptions['download_archive'] = None

    for nIdx, sVideoUrl in enumerate(page.videos):
        if page.sUrlType == 'playlist':
            print(f"Processing playlist video {nIdx + 1} of {page._nVideos} :: {sVideoUrl}")
            print()

        # Get the actual video stream info for a video link from a playlist
        if page.sUrlType == 'playlist':
            pageVideo = Page_Pornve(sVideoUrl)
            sVideoName = pageVideo._sVideoName
            sVideoStreamUrl = pageVideo.videos[0]
            sPageUrl = pageVideo.url
        else:
            sVideoName = page._sVideoName
            sVideoStreamUrl = page.videos[0]
            sPageUrl = page.url

        bRun = True
        try:
            with open(sArchive) as archive:
                if sPageUrl in archive.read():
                    print(f"Archive already has an entry for {sPageUrl}")
                    print("Skipping...")
                    bRun = False
        except:
            pass

        if bRun:
            dYdlOptions['outtmpl'] = rf'.\\sites\\{sExtractor}\\{sVideoName}.%(ext)s'

            with youtube_dl.YoutubeDL(dYdlOptions) as ydl:
                ydl.cache.remove()
                ret = ydl.download([sVideoStreamUrl])

            # Need to do our own archiving since YTDL will treat everything with the name "index-v1-a1" because
            # of how the video is extracted in _extract_video_stream
            # YTDL ret 0 is good, 1 is bad
            if not ret:
                with open(sArchive, 'a') as archive:
                    archive.write(sPageUrl + "\r\n")

        if nVideoLimit is not None and (nIdx + 1) >= nVideoLimit:
            print(f"Hit the specified maximum limit of {nVideoLimit}. Stopping...")
            break
        print()
        sleepRandom(3, 5)


class Page_Pornve(dl_common.Page):

    def __init__(self, url):
        super().__init__(url)

        nPageStatus = self.content.status_code
        if nPageStatus != 200:
            if nPageStatus == 403:
                raise ConnectionError(f"403 Forbidden! Please check if cookies are required! Private videos/playlists cannot be accessed without cookies!")

        self.sUrlType = self._get_url_type()

        if self.sUrlType == 'video':
            sVideoStreamUrl = self._extract_video_stream()
            self.videos.append(sVideoStreamUrl)

            sVideoNameComponents = self.url.split('.html')[0].split('/')[-2:]
            self._sVideoName = '_'.join(reversed(sVideoNameComponents))

            self._nVideos = 1
        elif self.sUrlType == 'playlist':
            print("Playlist detected. Getting videos...")

            lUrlComponents = self.url.split('/')
            self._playlistId = lUrlComponents[-2] if not lUrlComponents[-1] else lUrlComponents[-1]

            self._extract_video_urls()
            self._nVideos = len(self.videos)
            print(f"Found {self._nVideos} video URLs in the playlist\r\n")


    def _get_url_type(self):
        if '/playlist/' in self.url:
            sUrlType = 'playlist'
        else:
            sUrlType = 'video'
        return sUrlType


    def _extract_video_urls(self, sFilter=None):
        """
        Extract video URLs from all playlist pages.
        """
        self._sUrlBaseFormat = f"https://pornve.com/?hide_search=1&op=search&playlist={self._playlistId}&sort_field=file_created&sort_order=down&page={{}}"

        lUrlVideos = []
        nPage = 0
        while True:
            nPage += 1

            lPageVideos = self._extract_page_urls(nPage)
            if lPageVideos:
                lUrlVideos += lPageVideos
                print(f"Found {len(lPageVideos)} videos on page {nPage:02}...")
            else:
                print(f"No videos found on page {nPage}. Stopping...")
                break
        self.videos += lUrlVideos


    def _extract_page_urls(self, nPage, sFilter=None):
        """
        Extract video URLs from a single page of the playlist.
        """
        dl_common.randomizeHeader()
        for nAttempts in range(3):
            sUrlPage = self._sUrlBaseFormat.format(nPage)
            content = dl_common.session.get(sUrlPage, headers=dl_common.dHeaders, cookies=dl_common.dCookiesParsed)
            if "503 Service Temporarily Unavailable" in content.text:
                if DEBUG:
                    print("503 encountered! Sleeping...")
                sleepRandom()
                continue
            soup = dl_common.BeautifulSoup(content.text, 'html.parser')
            sleepRandom(1, 3)
            break

        lVideos = []
        lProcessed = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href in lProcessed:
                continue
            if f'?list={self._playlistId}' not in href:
                continue
            if sFilter is not None and sFilter not in href:
                continue
            if href not in self.videos:
                sCleanedUrl = self._clean_video_url(href)
                if sCleanedUrl is not None and sCleanedUrl not in lVideos:
                    lVideos.append(sCleanedUrl)
                lProcessed += [href]
        return lVideos


    def _extract_video_stream(self):
        for nAttempts in range(3):
            content = dl_common.session.get(self.url, headers=dl_common.dHeaders, cookies=dl_common.dCookiesParsed)
            if "503 Service Temporarily Unavailable" in content.text:
                if DEBUG:
                    print("503 encountered! Sleeping...")
                sleepRandom()
                continue
            sleepRandom(1, 3)
            break

        sPackedCode = self._js_find_packed_code(content.text)
        sVideoStreamUrl = self._js_unpack_and_get_stream(sPackedCode)

        return sVideoStreamUrl


    def _clean_video_url(self, sUrlMasked, nAttempts=3):
        """
        Unmask playlist videos.
        """
        return sUrlMasked.split("?list=")[0]


    def _js_find_packed_code(self, htmlContent):
        lHtmlLines = htmlContent.split("\r\n")
        sPackedCode = None
        for row in lHtmlLines:
            if r"""eval(function(p,a,c,k,e,d)""" in row:
                sPackedCode = row
        if sPackedCode is None:
            raise ValueError("Did not find any packed JS code...")

        nIdxStart = len(sPackedCode) - len(sPackedCode.lstrip())
        sPackedCode = sPackedCode[nIdxStart:]

        if sPackedCode[-1:] == '\n':
            sPackedCode = sPackedCode[:-1]

        return sPackedCode


    def _js_unpack_and_get_stream(self, packedData):
        """
        Pass in obfuscated "eval(function(p,a,c,k,e,d)..." string
        """
        url = None
        unpacked_data = jsbeautifier.beautify(packedData).split('"')
        for sData in unpacked_data:
            if ".m3u8" in sData:
                url = sData
        if url is None:
            raise ValueError("Could not find a video stream URL!")

        # unpacked_data_split = unpacked_data.split('><source src=')
        # url = unpacked_data_split[1].split(""" type="application/x-mpegURL">""")[0].replace('"', "")

        return url


def urlStandardize(sUrl):
    """
    Make sure URL ends with '/' and tack on f-string brackets for iterating through pages.
    """
    if sUrl[-1] != '/':
        sUrl += '/'
    sUrl += '{}'
    return sUrl


def sleepRandom(nMin=5, nMax=10, bSim=False):
    """
    Sleep for some random interval to help avoid tripping Cloudflare's anti-bot protection.
    """
    nSleep = round(random.uniform(min(nMin, nMax), max(nMin, nMax)), 2)
    if DEBUG or bSim:
        print(nSleep)
    if not bSim:
        sleep(nSleep)

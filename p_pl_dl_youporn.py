from time import sleep
from time import time
import yt_dlp as youtube_dl

import p_pl_dl_common as dl_common

sExtractor = 'youporn'


def run(sUrl, sCookieSource=None, nVideoLimit=None, bDebug=False):
    print(f"Running {sExtractor} extractor for {sUrl}\r\n")

    if sCookieSource is not None:
        dl_common.parseCookieFile(sCookieSource)

    if dl_common.dCookiesParsed is None:
        print("WARNING :: No cookies were provided! Private videos/playlists will fail to download!\r\n")

    # Attempt initial connection
    html = dl_common.session.get(sUrl, headers=dl_common.dHeaders, cookies=dl_common.dCookiesParsed)
    print(f"Initial connection status: {html.status_code}")
    if html.status_code == 403:
        raise ConnectionError(f"403 Forbidden! Please check if cookies are required! Private videos/playlists cannot be accessed without cookies!")
    elif html.status_code != 200:
        raise ConnectionError(f"Initial connection failed : Status {html.status_code}")
    print()

    if bDebug:
        # Save HTML content to a text file for debug
        text_file = open("html_content.txt", "w", encoding='utf-8')
        text_file.write(html.text)
        text_file.close()

    page = Page_Youporn(sUrl)

    dYdlOptions = dict(dl_common.dYdlOptions)
    dYdlOptions['download_archive'] = rf".\\sites\\{sExtractor}\\{dYdlOptions['download_archive'].format(sExtractor)}"

    lFailedUrls = []

    def ytdlLoop(lUrls, bLogFailures):
        nonlocal lFailedUrls

        for nIdx, sVideoUrl in enumerate(lUrls):
            print(f"Processing video {nIdx + 1} of {len(lUrls)} :: {sVideoUrl}")
            print()

            sVideoId = sVideoUrl.split('view_video.php?viewkey=')[-1]
            dYdlOptions['outtmpl'] = rf'.\\sites\\{sExtractor}\\{sVideoId}_%(title).125s.mp4'

            nStart = time()
            try:
                with youtube_dl.YoutubeDL(dYdlOptions) as ydl:
                    ydl.download([sVideoUrl])
            except:
                if bLogFailures:
                    print(f"\r\nEncountered some error for URL = {sVideoUrl}")
                    print(f"Adding it to the retry list...")
                    lFailedUrls += [sVideoUrl]
                continue
            nStop = time()
            print(f"\r\nElapsed time for URL = {sVideoUrl}: {round((nStop - nStart) / 60, 2)} minutes\r\n")

            if nVideoLimit is not None and (nIdx + 1) >= nVideoLimit:
                print(f"Hit the specified maximum limit of {nVideoLimit}. Stopping...")
                break
        print()

    ytdlLoop(page.videos, bLogFailures=True)

    if lFailedUrls:
        print("Retrying URLs that failed...")
        for sUrl in lFailedUrls:
            print(sUrl)
        ytdlLoop(lFailedUrls, bLogFailures=False)


class Page_Youporn(dl_common.Page):

    def __init__(self, url):
        super().__init__(url)

        nPageStatus = self.content.status_code
        if nPageStatus != 200:
            if nPageStatus == 403:
                raise ConnectionError(f"403 Forbidden! Please check if cookies are required! Private videos/playlists cannot be accessed without cookies!")

        self.sUrlType = self._get_url_type()
        self._playlistId = self.url.split('.com/')[1].split('/')[0] if self.sUrlType == 'playlist' else None

        if self.sUrlType == 'video':
            self.videos.append(self.url)
            self._nVideos = 1
        elif self.sUrlType == 'playlist':
            print("Playlist detected. Getting videos...")
            self._sUrlBaseFormat = self.urlStandardize(self.url)
            self._extract_video_urls()
            self._nVideos = len(self.videos)
            print(f"Found {self._nVideos} video URLs in the playlist")


    def _get_url_type(self):
        if 'youporn.com/watch/' in self.url:
            sUrlType = 'video'
        elif 'youporn.com/favorites/' in self.url or 'youporn.com/collections/' in self.url:
            sUrlType = 'playlist'
        else:
            raise ValueError(f"Unable to determine {sExtractor} URL type for {self.url}! Please submit a bug report!")
        return sUrlType


    def _extract_video_urls(self, sFilter=None):
        """
        Extract video URLs from all playlist pages.
        """
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
        sUrlBase = "https://www.pornhub.com{}"

        for nAttempts in range(3):
            sUrlPage = self._sUrlBaseFormat.format(nPage)
            content = dl_common.session.get(sUrlPage, cookies=dl_common.dCookiesParsed)
            if "503 Service Temporarily Unavailable" in content.text:
                sleep(3)
                continue
            soup = dl_common.BeautifulSoup(content.text, 'html.parser')
            break

        lVideos = []
        lTags = soup.find_all(attrs={"class": 'pcVideoListItem js-pop videoblock videoBox'})
        for tag in lTags:
            if 'id' in tag.attrs.keys() and 'vfavouriteVideo' in tag.attrs['id']:
                for a in tag.find_all('a', href=True):
                    href = a['href']
                    if 'view_video.php?' not in href:
                        continue
                    if '&pkey=' in href:
                        continue
                    if href not in self.videos:
                        sUrlFull = sUrlBase.format(href)
                        if sUrlFull not in lVideos:
                            lVideos.append(sUrlFull)
        return lVideos


    def urlStandardize(self, sUrl):
        """
        Make sure URL ends with '/' and tack on f-string brackets for iterating through pages.
        """
        if sUrl.endswith('favorites'):
            sUrl += '?page={}'
        return sUrl

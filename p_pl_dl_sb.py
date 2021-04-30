from time import sleep
import youtube_dl

import p_pl_dl_common as dl_common

sExtractor = 'spankbang'


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

    page = Page_Spankbang(sUrl)

    dYdlOptions = dict(dl_common.dYdlOptions)
    dYdlOptions['download_archive'] = rf".\\sites\\{sExtractor}\\{dYdlOptions['download_archive'].format(sExtractor)}"

    for nIdx, sVideoUrl in enumerate(page.videos):
        if page.sUrlType == 'playlist':
            print(f"Processing playlist video {nIdx + 1} of {page._nVideos} :: {sVideoUrl}")
            print()

        dYdlOptions['outtmpl'] = rf'.\\sites\\{sExtractor}\\%(title)s.%(ext)s'

        with youtube_dl.YoutubeDL(dYdlOptions) as ydl:
            ydl.download([sVideoUrl])

        if nVideoLimit is not None and (nIdx + 1) >= nVideoLimit:
            print(f"Hit the specified maximum limit of {nVideoLimit}. Stopping...")
            break
        print()


class Page_Spankbang(dl_common.Page):

    def __init__(self, url):
        super().__init__(url)

        nPageStatus = self.content.status_code
        if nPageStatus != 200:
            if nPageStatus == 403:
                raise ConnectionError(f"403 Forbidden! Please check if cookies are required! Private videos/playlists cannot be accessed without cookies!")

        self.sUrlType = self._get_url_type()
        self._playlistId = self.url.split('.com/')[1].split('/')[0] if self.sUrlType == 'playlist' else None
        self._sUrlBaseFormat = urlStandardize(self.url)

        if self.sUrlType == 'video':
            self.videos.append(self.url)
            self._nVideos = 1
        elif self.sUrlType == 'playlist':
            print("Playlist detected. Getting videos...")
            self._extract_video_urls()
            self._nVideos = len(self.videos)
            print(f"Found {self._nVideos} video URLs in the playlist")


    def _get_url_type(self):
        # Video URLs are in the form of spankbang.com/vwxyz/video/full-content-name
        # Playlists are in the form of spankbang.com/ijklm/playlist/name-of-playlist
        # Within a playlist, its videos are "masked" as spankbang.com/ijklm-abc123/playlist/name-of-playlist
        if '/video/' in self.url:
            sUrlType = 'video'
        elif '/playlist/' in self.url:
            if '-' in self.url:
                sUrlType = 'video_masked'
            else:
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
        for nAttempts in range(3):
            sUrlPage = self._sUrlBaseFormat.format(nPage)
            content = dl_common.session.get(sUrlPage, cookies=dl_common.dCookiesParsed)
            if "503 Service Temporarily Unavailable" in content.text:
                sleep(3)
                continue
            soup = dl_common.BeautifulSoup(content.text, 'html.parser')

        lVideos = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if 'playlist' not in href:
                continue
            if '/lang/' in href:
                continue
            if f'{self._playlistId}-' not in href:
                continue
            if sFilter is not None and sFilter not in href:
                continue
            if href not in self.videos:
                sUnmaskedUrl = self._unmask_video_url(a['href'])
                if sUnmaskedUrl is not None and sUnmaskedUrl not in lVideos:
                    lVideos.append(sUnmaskedUrl)
        return lVideos


    def _unmask_video_url(self, sUrlMasked, nAttempts=3):
        """
        Unmask playlist videos.
        """
        sUrlFull = rf"https://spankbang.com{sUrlMasked}"

        # Load up the page using the masked URL, then search its content for the real URL
        for nAttempt in range(nAttempts):
            content = dl_common.session.get(sUrlFull, cookies=dl_common.dCookiesParsed)
            soup = dl_common.BeautifulSoup(content.text, 'html.parser')

            try:
                sCanonicalUrl = soup.find(attrs={'rel': 'canonical'}).attrs['href']
            except:
                sCanonicalUrl = None

            if sCanonicalUrl is not None:
                break
            else:
                sleep(1)

        if sCanonicalUrl is None:
            print(f"Failed to unmask a URL for {sUrlMasked}")
        return sCanonicalUrl


def urlStandardize(sUrl):
    """
    Make sure URL ends with '/' and tack on f-string brackets for iterating through pages.
    """
    if sUrl[-1] != '/':
        sUrl += '/'
    sUrl += '{}'
    return sUrl

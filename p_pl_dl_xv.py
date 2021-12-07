import yt_dlp as youtube_dl

import p_pl_dl_common as dl_common

sExtractor = 'xvideos'


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

    page = Page_Xvideos(sUrl)
    nPageStatus = page.content.status_code
    if nPageStatus != 200:
        if nPageStatus == 403:
            raise ConnectionError(f"403 Forbidden! Please check if cookies are required! Private videos/playlists cannot be accessed without cookies!")

    dYdlOptions = dict(dl_common.dYdlOptions)
    dYdlOptions['download_archive'] = rf".\\sites\\{sExtractor}\\{dYdlOptions['download_archive'].format(sExtractor)}"

    print()
    for nIdx, sVideoUrl in enumerate(page.videos):
        if page.sUrlType == 'playlist':
            print(f"Processing playlist video {nIdx + 1} of {len(page.videos)} :: {sVideoUrl}")
            print()

        dYdlOptions['outtmpl'] = rf'.\\sites\\{sExtractor}\\%(title).125s.%(ext)s'

        with youtube_dl.YoutubeDL(dYdlOptions) as ydl:
            ydl.download([sVideoUrl])

        if nVideoLimit is not None and (nIdx + 1) >= nVideoLimit:
            print(f"Hit the specified maximum limit of {nVideoLimit}. Stopping...")
            break
        print()


class Page_Xvideos(dl_common.Page):

    def __init__(self, url):
        super().__init__(url)
        if f'{sExtractor}.com/video' in self.url:
            sUrlType = 'video'
        elif f'{sExtractor}.com/favorite' in self.url:
            sUrlType = 'playlist'
        else:
            raise ValueError(f"Unable to determine {sExtractor} URL type for {self.url}! Please submit a bug report!")
        self.sUrlType = sUrlType

        self._sUrlBaseFormat = urlStandardize(self.url)

        if self.sUrlType == 'video':
            self.videos.append(self.url)
        elif self.sUrlType == 'playlist':
            print("Playlist detected. Getting videos...")
            self._extract_video_urls()


    def _extract_video_urls(self, sFilter=None):
        """
        Extract video URLs from all playlist pages.
        """
        nNumPages = self._NumPagesGet()
        print(f"Found {nNumPages} pages in the playlist...")

        lUrlVideos = []
        for nPage in range(0, nNumPages):
            lPageVideos = self._extract_page_urls(nPage)
            if lPageVideos:
                lUrlVideos += lPageVideos
                print(f"Found {len(lPageVideos)} on page {nPage + 1}")
            else:
                print(f"Failed to load page {nPage + 1}!")
                break

        # Remove non-video URLs that may have been picked up
        lTemp = []
        for sUrl in lUrlVideos:
            if 'com/videos/recommended' in sUrl:
                continue
            if 'com/video' in sUrl:
                lTemp += [sUrl]
            else:
                raise ValueError(f"Not sure about this one: {sUrl}")
        lUrlVideos = lTemp

        nNumVideos = len(lUrlVideos)
        print(f"\r\nFound {nNumVideos} video URLs in the playlist")
        self.videos += lUrlVideos


    def _extract_page_urls(self, nPage, sFilter=None):
        """
        Extract video URLs from a single playlist page.
        """
        sUrlPage = self._sUrlBaseFormat.format(nPage)
        content = dl_common.session.get(sUrlPage, cookies=dl_common.dCookiesParsed)
        soup = dl_common.BeautifulSoup(content.text, 'html.parser')

        lVideos = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/video' != href[:6]:
                continue
            if '/videos-i-like' == href:
                continue

            if sFilter is not None and sFilter not in href:
                continue

            sVideoUrlFull = 'https://www.xvideos.com' + a['href']
            sVideoUrlSplit = sVideoUrlFull.split('?pl=')[0]

            if sVideoUrlSplit not in lVideos:
                lVideos.append(sVideoUrlSplit)
        return lVideos


    def _NumPagesGet(self):
        """
        Return the number of pages in the playlist.
        """
        pagination_block = self.soup.find(attrs={"class": 'pagination'})

        # Check for playlist with many pages first (i.e. pagination of pages)
        try:
            nPages = int(pagination_block.find(attrs={"class": "last-page"}).string)
        except:
            # Then for a multi-page playlist (no pagination of pages)
            try:
                nPages = len(pagination_block.find_all('li')) - 1
            # If no pagination, assume only one page
            except AttributeError:
                nPages = 1
        return nPages


def urlStandardize(sUrl):
    """
    Make sure URL ends with '/' and tack on f-string brackets for iterating through pages.
    """
    if sUrl[-1] != '/':
        sUrl += '/'
    sUrl += '{}'
    return sUrl

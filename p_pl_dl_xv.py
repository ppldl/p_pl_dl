import youtube_dl

import p_pl_dl_common as dl_common

sExtractor = 'xvideos'


def run(sUrl, sCookieSource=None, nVideoLimit=None, bDebug=False):
    print(f"Running {sExtractor} extractor for {sUrl}\r\n")

    if sCookieSource is not None:
        dl_common.parseCookieFile(sCookieSource)

    if dl_common.dCookiesParsed is None:
        print("WARNING :: No cookies were provided! Private videos/playlists will fail to download!\r\n")

    if f'{sExtractor}.com/video' in sUrl:
        sUrlType = 'video'
    elif f'{sExtractor}.com/favorite' in sUrl:
        sUrlType = 'playlist'
    else:
        raise ValueError(f"Unable to determine {sExtractor} URL type for {sUrl}! Please submit a bug report!")

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

    lUrlVideos = []
    if sUrlType == 'playlist':
        print("Playlist detected. Getting videos...")
        page = Page_Xvideos(sUrl)
        nPageStatus = page.content.status_code
        if nPageStatus != 200:
            if nPageStatus == 403:
                raise ConnectionError(f"403 Forbidden! Please check if cookies are required! Private videos/playlists cannot be accessed without cookies!")

        nNumPages = page._NumPagesGet()
        sUrlBaseFormat = urlStandardize(sUrl)
        print(f"Found {nNumPages} pages in the playlist...")

        for nPage in range(0, nNumPages):
            page = Page_Xvideos(sUrlBaseFormat.format(nPage))
            page._extract_video_urls()
            if page.videos:
                lUrlVideos += page.videos
                print(f"Found {len(page.videos)} on page {nPage + 1}")
            else:
                break

        # Remove non-video URLs that may have been picked up
        lTemp = []
        for sUrl in lUrlVideos:
            if 'com/videos/recommended' in sUrl:
                continue
            if 'com/video' in sUrl:
                lTemp += [sUrl]
        lUrlVideos = lTemp

        nNumVideos = len(lUrlVideos)
        print(f"Found {nNumVideos} video URLs in the playlist")
        if bDebug:
            for sUrl in lUrlVideos:
                print(sUrl)

    elif sUrlType == 'video':
        lUrlVideos = [sUrl]

    dYdlOptions = dict(dl_common.dYdlOptions)
    dYdlOptions['download_archive'] = rf".\\sites\\{sExtractor}\\{dYdlOptions['download_archive'].format(sExtractor)}"

    for nIdx, sVideoUrl in enumerate(lUrlVideos):
        if sUrlType == 'playlist':
            print(f"Processing playlist video {nIdx + 1} of {nNumVideos} :: {sVideoUrl}")
            print()

        dYdlOptions['outtmpl'] = rf'.\\sites\\{sExtractor}\\%(title)s.%(ext)s'

        with youtube_dl.YoutubeDL(dYdlOptions) as ydl:
            ydl.download([sVideoUrl])

        if nVideoLimit is not None and (nIdx + 1) >= nVideoLimit:
            print(f"Hit the specified maximum limit of {nVideoLimit}. Stopping...")
            break
        print()


class Page_Xvideos(dl_common.Page):

    def _extract_video_urls(self, sFilter=None):
        for a in self.soup.find_all('a', href=True):
            href = a['href']
            if '/video' != href[:6]:
                continue
            if '/videos-i-like' == href:
                continue
            if sFilter is not None and sFilter not in href:
                continue

            if href not in self.videos:
                sVideoUrlFull = 'https://www.xvideos.com' + a['href']
                sVideoUrlSplit = sVideoUrlFull.split('?pl=')[0]
                self.videos.append(sVideoUrlSplit)


    def _NumPagesGet(self):
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

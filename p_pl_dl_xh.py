import yt_dlp as youtube_dl

import p_pl_dl_common as dl_common

sExtractor = 'xhamster'

# Something changed with xhamster where these headers are now required
def _xhamsterHeaderGet():
    dHeaders_xh = {'Host'           : 'xhamster.com',
                   'User-Agent'     : dl_common.randomizeUserAgent(),
                   'DNT'            : '1',
                   'Connection'     : 'keep-alive',
                   'Sec-Fetch-Dest' : 'document',
                   'Sec-Fetch-Mode' : 'navigate',
                   'Sec-Fetch-Site' : 'none',
                   'Sec-Fetch-User' : '?1',
                   'Cache-Control'  : 'max-age=0',
                   'Cookie'         : dl_common.cookieHeaderStringGet(),
                   'TE'             : 'trailers'
                   }
    return dHeaders_xh


def run(sUrl, sCookieSource=None, nVideoLimit=None, bDebug=False):
    print(f"Running {sExtractor} extractor for {sUrl}\r\n")

    if sCookieSource is not None:
        dl_common.parseCookieFile(sCookieSource)

    if dl_common.dCookiesParsed is None:
        print("WARNING :: No cookies were provided! Private videos/playlists will fail to download!\r\n")

    if f'{sExtractor}.com/videos' in sUrl:
        sUrlType = 'video'
    elif f'{sExtractor}.com/my' in sUrl:
        sUrlType = 'playlist'
    else:
        raise ValueError(f"Unable to determine {sExtractor} URL type for {sUrl}! Please submit a bug report!")

    dXhamsterHeader = _xhamsterHeaderGet()

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
        sUrlBaseFormat = urlStandardize(sUrl)
        nPage = 0
        while True:
            nPage += 1
            print(f"Attempting page {nPage:02}")
            sUrlPage = sUrlBaseFormat.format(f'{nPage:02}')
            page = dl_common.Page(sUrlPage, headers=dXhamsterHeader)
            nPageStatus = page.content.status_code
            if nPageStatus != 200:
                if nPageStatus == 403:
                    raise ConnectionError(f"403 Forbidden! Please check if cookies are required! Private videos/playlists cannot be accessed without cookies!")
                elif nPageStatus == 404:
                    print(f"Page {nPage} returned 404!")
                    print(f"Assuming page {nPage - 1} was the last page of the playlist")
                    break

            if "<title>Page not found</title>" in page.content.text:
                break

            page._extract_video_urls()
            if page.videos:
                lUrlVideos += page.videos
            else:
                break

        # Remove non-video URLs that may have been picked up
        lTemp = []
        for sUrl in lUrlVideos:
            if 'com/videos/recommended' in sUrl:
                continue
            if 'com/videos' in sUrl:
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


def urlStandardize(sUrl):
    """
    Make sure URL ends with '/' and tack on f-string brackets for iterating through pages.
    """
    if sUrl[-1] != '/':
        sUrl += '/'
    sUrl += '{}'
    return sUrl

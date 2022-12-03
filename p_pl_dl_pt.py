from time import time
import yt_dlp as youtube_dl

import p_pl_dl_common as dl_common

sExtractor = 'porntrex'


"""
For PornTrex, Youtube-DL does not seem able to consistently pick the highest
quality source. To workaround this, I pull the entire video page and pick the 
largest file available from its download options, and pass that URL to Youtube-DL.

PornTrex also uses AJAX, which is a bit awkward to deal with for me.
"""


def run(sUrl, sCookieSource=None, nVideoLimit=None, bDebug=False):
    print(f"Running {sExtractor} extractor for {sUrl}\r\n")

    nTimeStart = time()

    if sCookieSource is not None:
        dl_common.parseCookieFile(sCookieSource)

    if dl_common.dCookiesParsed is None:
        print("WARNING :: No cookies were provided! Private videos/playlists will fail to download!\r\n")

    if 'porntrex.com/video' in sUrl:
        sUrlType = 'video'
    elif 'porntrex.com/my' in sUrl:
        sUrlType = 'playlist'
    elif 'porntrex.com/search' in sUrl:
        sUrlType = 'playlist'               # Search results can be treated as a playlist
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
        sUrlBaseFormat = urlBaseFormatGet(sUrl)
        nPage = 0

        while True:
            nPage += 1
            print(f"Attempting page {nPage:02}")
            if 'search' in sUrl:
                if nPage == 1:
                    sUrlPage = sUrlBaseFormat.format('')
                else:
                    sUrlPage = sUrlBaseFormat.format(f'{nPage}/')
            else:
                sUrlPage = sUrlBaseFormat.format(f'{nPage:02}')
            page = dl_common.Page(sUrlPage)
            nPageStatus = page.content.status_code
            if nPageStatus != 200:
                if nPageStatus == 403:
                    raise ConnectionError(f"403 Forbidden! Please check if cookies are required! Private videos/playlists cannot be accessed without cookies!")
                elif nPageStatus == 404:
                    print(f"Page {nPage} returned 404!")
                    print(f"Assuming page {nPage - 1} was the last page of the playlist")
                    break
            page._extract_video_urls()
            if page.videos:
                lUrlVideos += page.videos
            else:
                break

        # Remove non-video URLs that may have been picked up
        lTemp = []
        for sUrl in lUrlVideos:
            if sUrl == 'https://www.porntrex.com/my/favourites/videos/':
                continue
            if 'video' in sUrl:
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
            print(f"Processing video {nIdx + 1} of {nNumVideos}...")
            print()

        if bDebug:
            print(f"Processing {sVideoUrl}")
        video = Video(sVideoUrl)
        dYdlOptions['outtmpl'] = rf'.\\sites\\{sExtractor}\\{video.sFullName}'

        with youtube_dl.YoutubeDL(dYdlOptions) as ydl:
            ydl.download([video.downloadUrl])

        if nVideoLimit is not None and (nIdx + 1) >= nVideoLimit:
            print(f"Hit the specified maximum limit of {nVideoLimit}. Stopping...")
            break
        print()

    nTimeEnd = time()
    print(f"Run time: {round((nTimeEnd - nTimeStart) / 60, 2)} minutes")


def urlBaseFormatGet(sUrl):
    """
    Create the base f-string URL that be used to iteratively go through pages.

    Playlists and favorites use an AJAX format. They do not have simple page numbers.
    Search results use simple page numbers.
    """
    sUrlBase = None
    if 'playlists' in sUrl:
        print("Using 'playlists' format...")
        nType = 10
        nPlaylistId = sUrl.split('/')[-2]
        sUrlBase = f'https://www.porntrex.com/my/playlists/{nPlaylistId}/?mode=async&function=get_block&block_id=list_videos_my_favourite_videos&fav_type={nType}&playlist_id={nPlaylistId}&sort_by=&from_my_fav_videos={{}}'
    elif 'favourites' in sUrl:
        print("Using 'favourites' format...")
        nType = 0
        nPlaylistId = 0
        sUrlBase = f'https://www.porntrex.com/my/favourites/videos/?mode=async&function=get_block&block_id=list_videos_my_favourite_videos&fav_type={nType}&playlist_id={nPlaylistId}&sort_by=&from_my_fav_videos={{}}'
    elif 'search' in sUrl:
        if not sUrl.endswith('/'):
            sUrl += '/'
        sUrl += '{}'
        sUrlBase = sUrl
    return sUrlBase


class Video(dl_common.Page):

    def __init__(self, url):
        super().__init__(url)
        self.downloadUrl = None

        lUrlComponents = self.url.split('/')
        if lUrlComponents[-1] == '':
            lUrlComponents.pop(-1)
        self._lUrlComponents = lUrlComponents

        self.sVideoId   = self._lUrlComponents[-2]
        self.sVideoName = self._lUrlComponents[-1]
        self.sFullName  = '_'.join([self.sVideoId, self.sVideoName]) + '.mp4'

        self._extract_video_urls(sFilter='get_file')
        self._extract_video_largest()


    def _extract_video_largest(self):
        """
        Get the file that has the largest file size, which should be the highest quality.
        """
        nIdxBiggest = 0
        nBiggestSize = 0
        for index in range(len(self.videos)):
            nSize = int(dl_common.session.get(self.videos[index], cookies=dl_common.dCookiesParsed, stream=True).headers['Content-Length'])
            if nSize > nBiggestSize:
                nIdxBiggest = index
                nBiggestSize = nSize
        self.downloadUrl = self.videos[nIdxBiggest]

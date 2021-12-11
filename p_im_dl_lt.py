import os

import p_pl_dl_common as dl_common

sExtractor = 'lewdthots'

sTestUrl = r"https://lewdthots.com/meg-turney-lord-raiden-topless-onlyfans-set-leaked/"


def run(sUrl, *args, **kwargs):
    print(f"Running {sExtractor} extractor for {sUrl}\r\n")

    html = dl_common.session.get(sUrl, headers=dl_common.dHeaders)

    soup = dl_common.BeautifulSoup(html.text, 'html.parser')
    eGallery = soup.find(attrs={"class": 'mace-gallery-teaser'})        # Get gallery element into soup
    lGallery = eval(eGallery.attrs['data-g1-gallery'])                  # Should eval to a list of dicts

    lImageUrls = []
    for dImage in lGallery:
        sImageUrl = dImage['full']
        sImageUrl = sImageUrl.replace("\\", "")
        lImageUrls += [sImageUrl]
    print(f"Found {len(lImageUrls)} images")

    sArchive = rf".\\sites\\{sExtractor}\\dl_hist_{sExtractor}.txt"

    # Parse out album name, then check whether this album has already been downloaded
    sAlbumName = sUrl.split("/")[-2] if sUrl[-1] == '/' else sUrl.split("/")[-1]
    sAlbumName.replace("-", "_")

    bRun = True
    try:
        with open(sArchive) as archive:
            if sAlbumName in archive.read():
                print(f"Archive already has an entry for {sAlbumName}")
                print("Skipping...")
                bRun = False
    except:
        pass

    if bRun:
        # Create subdirectory for the album - there has to be a better (more Pythonic) way...
        lPathComponents = ['sites', sExtractor, sAlbumName]
        sPath = ''
        for idx, sPathComponent in enumerate(lPathComponents):
            sPath += sPathComponent
            try:
                os.mkdir(sPath)
            except Exception:
                pass
            sPath += '/'

        nImageNum = 1
        for sImageUrl in lImageUrls:
            sImageName = sImageUrl.split('/')[-1]
            print(f"Processing image {nImageNum:>03} : {sImageName}")
            nFileName = f"{nImageNum:>03}_{sImageName}"
            with open(os.path.join('sites', sExtractor, sAlbumName, nFileName), 'wb') as handler:
                response = dl_common.requests.get(sImageUrl, stream=True)
                handler.write(response.content)
            nImageNum += 1

        with open(sArchive, 'a') as archive:
            archive.write(sAlbumName + "\r\n")


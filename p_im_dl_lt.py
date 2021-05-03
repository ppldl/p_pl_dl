import os

import p_pl_dl_common as dl_common

sExtractor = 'lewdthots'

sTestUrl = r"https://lewdthots.com/meg-turney-lord-raiden-topless-onlyfans-set-leaked/"


def run(sUrl, *args, **kwargs):
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

    # Create subdirectory for the album - there has to be a better (more Pythonic) way
    sAlbumName = sUrl.split("/")[-2] if sUrl[-1] == '/' else sUrl.split("/")[-1]
    sAlbumName.replace("-", "_")
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

import os
import argparse
import json
import traceback
from time import sleep

import p_pl_dl_common as dl_common
import p_pl_dl_ph as dl_ph
import p_pl_dl_pt as dl_pt
import p_pl_dl_pornve as dl_pornve
import p_pl_dl_sb as dl_sb
import p_pl_dl_xh as dl_xh
import p_pl_dl_xv as dl_xv
import p_im_dl_lt as dl_lt


def main(argv):
    print()

    if argv.dest is not None:
        os.chdir(argv.dest)
    print(f"Working download directory: {os.getcwd()}")
    sleep(2)

    print()
    sSourceCookies = argv.cookies
    if sSourceCookies is not None:
        print(f"Cookies source: {sSourceCookies}")
        if ".txt'" in sSourceCookies:
            dl_common.parseCookieFile(sSourceCookies)
        else:
            dl_common.parseCookies(sSourceCookies)
    else:
        print(f"No cookies provided!")
    sleep(0.5)

    print()
    sSourceUrls = argv.input
    print(f"Using the following input source: {sSourceUrls}")
    print()
    sleep(0.5)

    dSites = {'lewdthots'   : False,
              'pornhub'     : False,
              'porntrex'    : False,
              'pornve'      : False,
              'spankbang'   : False,
              'xhamster'    : False,
              'xvideos'     : False,
              'youporn'     : False,
              }

    dExtractors = {'lewdthots'  : dl_lt,
                   'pornhub'    : dl_ph,
                   'porntrex'   : dl_pt,
                   'pornve'     : dl_pornve,
                   'spankbang'  : dl_sb,
                   'xhamster'   : dl_xh,
                   'xvideos'    : dl_xv,
                   }

    nVideoLimit = int(argv.limit) if argv.limit is not None else None
    print(f"Video limit per URL = {nVideoLimit}")

    # Get each URL into a dict
    dUrlDefs = {}
    with open(sSourceUrls) as fSourceUrls:
        sLines = fSourceUrls.readlines()
        for sLine in sLines:
            sUrl = sLine.strip()
            print(f"URL: {sUrl}")
            for sSite in dSites.keys():
                if sSite in sLine:
                    dSites[sSite] = True
                    dUrlDefs[sUrl] = sSite
    print()
    print("Detected websites:")
    print(json.dumps(dSites, indent=4))
    print()
    sleep(2)

    if argv.only is not None:
        argv.only = argv.only.lower()
        if argv.only in dSites.keys():
            for key, value in dSites.items():
                if argv.only == key:
                    dSites[key] = True
                else:
                    dSites[key] = False

    for sUrl, sSite in dUrlDefs.items():
        if sSite in dExtractors.keys() and dSites[sSite]:
            try:
                dExtractors[sSite].run(sUrl, sCookieSource=None, nVideoLimit=nVideoLimit)       # Cookies should already be parsed and available when going through main
            except:
                print("\r\n\r\n")
                traceback.print_exc()
                print("\r\n\r\n")
                continue
        else:
            print(f"No extractor available for {sSite} - {sUrl}")
            sleep(0.5)
        print()


if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-i', '--input',     help='Input TXT file with URLs to process', required=True)
    argparser.add_argument('-c', '--cookies',   help='Input TXT file with cookies')
    argparser.add_argument('-d', '--dest',      help='Download destination path')
    argparser.add_argument('-o', '--only',      help='Only run a specific site')
    argparser.add_argument('-l', '--limit',     help='Limit the number of videos')
    args = argparser.parse_args()
    main(args)

import os
import argparse
import json
from time import sleep

import p_pl_dl_common as dl_common
import p_pl_dl_pt as dl_pt
import p_pl_dl_xh as dl_xh


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

    dSites = {'pornhub'  : False,
              'porntrex' : False,
              'spankbang': False,
              'xhamster' : False,
              'xvideos'  : False,
              'youporn'  : False,
              }

    dExtractors = {'porntrex': dl_pt,
                   'xhamster': dl_xh,
                   }

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

    for sUrl, sSite in dUrlDefs.items():
        if sSite in dExtractors.keys():
            try:
                dExtractors[sSite].run(sUrl, sCookieSource=None)        # Cookies should already be parsed and available when going through main
            except Exception as e:
                print("\r\n\r\n")
                print(e)
                print("\r\n\r\n")
                continue
        else:
            print(f"No extractor available for {sSite} - {sUrl}")
        print()


if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-i', '--input',     help='Input TXT file with URLs to process', required=True)
    argparser.add_argument('-c', '--cookies',   help='Input TXT file with cookies')
    argparser.add_argument('-d', '--dest',      help='Download destination path')
    args = argparser.parse_args()
    main(args)

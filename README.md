# p_pl_dl - Porn Playlist Downloader

A porn playlist downloader using `youtube-dl` and `beautifulsoup`, along with some limited support for image albums.

Currently supports:

- lewdthots (albums only)
- pornhub
- porntrex
- spankbang
- xhamster
- xvideos

***
***

## Overview

#### Basic Usage

Call `p_pl_dl_main` using command prompt. Pass in a text file with URLs using `-i`. Optionally, provide cookies with `-c`, and specify the download destination with `-d`.

For cookies, you may pass in a single text file, or a folder path containing multiple cookie text files.

Videos from each site will be downloaded to `\sites\<site name>` within the current working directory.

Using a single cookie text file:
```
python p_pl_dl_main.py.py -i "C:\MyFolder\urls.txt" -c "C:\MyCookieFolder\cookies.txt" -d "F:\DownloadDestination"
```

Using multiple cookie text files stored in a folder:

```
python p_pl_dl_main.py.py -i "C:\MyFolder\urls.txt" -c "C:\MyCookieFolder\" -d "F:\DownloadDestination"
```

You may also restrict downloads to a specific site using `-o`. This may be useful if your `urls.txt` has lots of playlists/videos across many sites, but you need to scrape a specific one. Pass in the full name of the site as given in the list of supported sites above.

```
python p_pl_dl_main.py.py -i "C:\MyFolder\urls.txt" -c "C:\MyCookieFolder\" -d "F:\DownloadDestination" -o "xhamster"
python p_pl_dl_main.py.py -i "C:\MyFolder\urls.txt" -c "C:\MyCookieFolder\" -d "F:\DownloadDestination" -o "spankbang"
```

***

#### Input TXT w/ URLs

The URL text file should have URLs separated by a line break. The URLs may be for individual videos or entire playlists.

Example:

```
https://www.xvideos.com/video35247781/
https://www.xhamster.com/videos/busty-blonde-girl-get-fucked-with-nice-lingerie-14429903
```

#### Cookies

All cookie text files must have `# Netscape HTTP Cookie File` on its first line. If that line is not found, the file will not be recognized as a cookie file and ignored.

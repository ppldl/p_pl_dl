# p_pl_dl - Porn Playlist Downloader

A porn playlist downloader using `youtube-dl` and `beautifulsoup`.

Currently supports:

- porntrex
- xhamster
- xvideos

Future updates will add support for:
- pornhub
- spankbang
- youporn

***
***

## Overview

#### Basic Usage

Call `p_pl_dl_main` using command prompt. Pass in a text file with URLs using `-i`. Optionally, provide cookies with `-c`, and specify the download destination with `-d`.

For cookies, you may pass in a single text file, or a folder path containing multiple cookie text files.

Videos from each site will be downloaded to `\sites\<site name>` within the current working directory.

Using a single cookie text file:
```
python p_pl_dl_main.py.py -i "C:\MyFolder\TextFileWithUrls.txt" -c "C:\MyFolder\FolderWithCookieTxts\cookies.txt" -d "F:\WorkingDir"
```

Using multiple cookie text files stored in a folder:

```
python p_pl_dl_main.py.py -i "C:\MyFolder\TextFileWithUrls.txt" -c "C:\MyFolder\FolderWithCookieTxts" -d "F:\WorkingDir"
```

***

#### Input TXT w/ URLs

The URL text file should have URLs separated by a line break.

Example:

```
https://www.xvideos.com/video35247781/
https://www.xhamster.com/videos/busty-blonde-girl-get-fucked-with-nice-lingerie-14429903
```

#### Cookies

All cookie text files must have `# Netscape HTTP Cookie File` on its first line. If that line is not found, the file will not be recognized as a cookie file and ignored.

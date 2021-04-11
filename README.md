# p_pl_dl - Porn Playlist Downloader

A porn playlist downloader using `youtube-dl` and `beautifulsoup`.

Currently only supports porntrex and xhamster.

Future updates will add support for:

- pornhub
- spankbang
- xvideos
- youporn


## Usage

Pass in a text file with URLs. Optionally, provide cookies and specify the download destination.

Videos from each site will be downloaded to `\sites\<site name>` within the current working directory.

Using a single cookie text file:
```
python p_pl_dl_main.py.py -i "C:\MyFolder\TextFileWithUrls.txt" -c "C:\MyFolder\FolderWithCookieTxts\cookies.txt" -d "F:\DownloadDestination"
```

Using multiple cookie text files:

```
python p_pl_dl_main.py.py -i "C:\MyFolder\TextFileWithUrls.txt" -c "C:\MyFolder\FolderWithCookieTxts" -d "F:\DownloadDestination"
```

# owi2plex
Exporter of EPG from OpenWebif to XMLTV to use with Plex

## Dependencies
* Python 3.7
* OpenWebif Server (Such as Enigma2 box, OpenVix with OpenWebif plugin, ...)
* Plex (to use the XMLTV file)

## Installation
### Via PIP
run the following command:

`pip install owi2plex`

### Cloning this Repo
Clone this repository locally (suggest you do into a folder where your Plex server runs or at least where it can get the output file via a network mount/share).

Install the requirements with:

`pip install -r requirements.txt`

## Usage
```
owi2plex --help
Usage: owi2plex [OPTIONS]

Options:
  -b, --bouquet TEXT      The name of the bouquet to parse. If not specified
                          parse all bouquets.
  -u, --username TEXT     OpenWebIf Username
  -p, --password TEXT     OpenWebIf Password
  -h, --host TEXT         OpenWebIf Host
  -P, --port INTEGER      OpenWebIf Port
  -o, --output-file TEXT  Output file
  -l, --list-bouquets     Display a list of bouquets.
  --help                  Show this message and exit.
```

## Examples

If OpenWebif server is running in 192.168.0.150:80 with no auth and you want to output the file to c:\tmp\:

`owi2plex -h 192.168.0.150 -o c:\\tmp\\epg.xml`

If you have a bouquet called TV and you only want to generate the XMLTV for the channels in that bouquet:

`./owi2plex -b TV -h 192.168.0.150 -o /tmp/epg.xml`

## Scheduling

For now the script doesn't handle scheduling but you can use crontab in Linux or Windows' Task Scheduler. Ensure that the script runs daily *after* your OpenWebif box has refreshed the EPG.

Depending on your machine and network speed the generation time varies but for my modest set-up it takes about 45 seconds for a bouquet with 100+ channels.

Enjoy
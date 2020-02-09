# owi2plex
Exporter of EPG from OpenWebif to XMLTV to use with Plex

## Dependencies
* Python 3.7
* The following Enigma2 Plugins need to be installed 
  * OpenWebif Server Plugin
  * HRTunerProxy Pluging
* Plex (to use the XMLTV file) with a Premium Subscription

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
  -b, --bouquet              TEXT     The name of the bouquet to parse. If not specified
                                      parse all bouquets.
  -u, --username             TEXT     OpenWebIf username.
  -p, --password             TEXT     OpenWebIf password.
  -h, --host                 TEXT     OpenWebIf host.
  -P, --port                 INTEGER  OpenWebIf port.
  -o, --output-file          TEXT     Output file.
  -c, --continuous-numbering BOOLEAN  Continuous numbering across bouquets.
  -l, --list-bouquets                 Display a list of bouquets.
  -V, --version                       Displays the version of the package.
  -O, --category-override    TEXT     Category override YAML file. See documentation for file format.
  --help                              Show this message and exit.
```

## Examples

If OpenWebif server is running in 192.168.0.150:80 with no auth and you want to output the file to c:\tmp\:

`owi2plex -h 192.168.0.150 -o c:\\tmp\\epg.xml`

If you have a bouquet called TV and you only want to generate the XMLTV for the channels in that bouquet:

`./owi2plex -b TV -h 192.168.0.150 -o /tmp/epg.xml`

## Scheduling

For now the script doesn't handle scheduling but you can use crontab in Linux or Windows' Task Scheduler. Ensure that the script runs daily *after* your OpenWebif box has refreshed the EPG.

Depending on your machine and network speed the generation time varies but for my modest set-up it takes about 45 seconds for a bouquet with 100+ channels.

## Program Category Overrides
You can specify a YAML override file to force the category for programms with specific title patterns as the EPG providers and OpenWebIf don't provide accurate categories in many cases. For example, give the following cat_overrides.yml file:

```
News: 
  - "News: One O'Clock"
  - "News: Six One"
  - "News: Nine O'Clock"
  - "ITV News:"
  - "Weather for the Week Ahead"
  - "BBC News"

Sports:
  - "Champions League"
  - "Cycling:"
  - "The NFL Show"
  - "NFL This Week"

Football: 
  - "Champions League"

Series:
  - "The NFL Show"
  - "NFL This Week"

```

you can run the following command: 

`./owi2plex -b TV -h 192.168.0.150 -o /tmp/epg.xml -O ./cat_overrides.yml`

To assign one or more categories to programs based on their title.

Please note the following:

* The file needs to be UTF-8 encoded, specially if the title patterns include special characters.
* The overrides are *not* appended to the categories in the EPG. In other words, if the title matches an override pattern it'll ignore the catogries parsed from the EPG.
* The titles are matched partially. For example, in the case of the file above, programs titled `Champions League Magazine` and `Champions League Live Tonight` with have their categories overriden.
* The title patterns are *not* case sensitve.


Enjoy

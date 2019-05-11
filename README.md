# Description
This project is used to get player's ranking from the website of the swiss badminton federation (https://www.swiss-badminton.ch)

# Usage
python3 ranking.py --playerid=123,345,546 [--slack] [--stdout]

## playerid
a coma separated list of player id. These id's can be found on the swiss-badminton website URL. For exemple, when seeing the information of player Yves Bovard, the URL is: https://www.swiss-badminton.ch/ranking/player.aspx?id=18623&player=2836215

The player id is then 2836215

## slack
when publishing the ranking on slack, the environment variable SLACK_WEBHOOK have to be setted

# Docker
## build image
```
docker build -t swissbadminton_ranking:latest -f docker/Dockerfile .
```

## container usage
```
docker run swissbadminton_ranking:latest --playerid=1234567,7654321 --syslog
```
```
docker run --env SLACK_WEBHOOK=https://hooks.slack.com/services/AAAAAA/BBBBB/CCCCCC swissbadminton_ranking:latest --playerid=1234567,7654321 --syslog --slack
```

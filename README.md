# Description
This project is used to get player's ranking from the website of the swiss badminton federation (https://www.swiss-badminton.ch)

# Usage
python3 ranking.py --playerid=123,345,546 [--slack] [--stdout] [--sqs=<endpoint> --aws-region=<AWS Region> --aws-host=<AWS host>] 

## playerid
a coma separated list of player id. These id's can be found on the swiss-badminton website URL. For exemple, when seeing the information of player Yves Bovard, the URL is: https://www.swiss-badminton.ch/ranking/player.aspx?id=18623&player=2836215

The player id is then 2836215

## slack
when publishing the ranking on slack, the environment variable SLACK_WEBHOOK have to be setted

## sqs
the value of "--sqs" should be the full endpoint, for example: http://localhost:9324/queue/myqueue. If using Amazon SQS, then aws-region and aws-host must be setted as well. The credentials should be added to files. The path can be specified by --aws-access-key and --aws-secret-access-key. Only the corresponding value should be in these files. By default --aws-access-key is /tmp/.aws-access-key and --aws-secret-access-key is /tmp/.aws-secret-access-key

## encryption
On some output method, there is possible to encrypt data using the --encryption parameter. This parameter, if set, points to a file container the encryption key to use. If not setted, the data are sent unencrypted.

Output method which allows encryption:
* sqs

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

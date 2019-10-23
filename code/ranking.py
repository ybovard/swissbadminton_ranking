import configparser
import asyncio
import aiohttp
import logging
from bs4 import BeautifulSoup
import argparse
import os
import sys
from aioslacker import Slacker
import datetime
import json
from pathlib import Path
import urllib
import aiosqs
from simplecrypt import encrypt, decrypt
from base64 import b64encode
import player_pb2

#https://www.swiss-badminton.ch/ranking/player.aspx?id=18623&player=2836215
#https://www.swiss-badminton.ch/ranking/ranking.aspx?rid=209
URL_SWISSBADMINTON='https://www.swiss-badminton.ch'
URL_SWISSBADMINTON_RANKING=URL_SWISSBADMINTON+'/ranking'
IDYEAR_SWISSBADMINTON=21780
RID=209

class PLAYER_CHAIN():
    PLAYER=None
    nextPlayer=None
    nextSingle=None
    nextDouble=None
    nextMixed=None

class RANK():
    POSITION=0
    POINT=0

class PLAYER():
    ID=0
    ERRORMSG=None
    LICENCE=0
    FULLNAME='Player Name'
    GENDER=''
    SINGLE=None
    DOUBLE=None
    MX=None


    def __str__(self):
        str="{}[{}]:".format(self.FULLNAME,self.LICENCE)
        if self.GENDER=='M':
            str+=" MS: {}({}pts), HD: {}({}pts), MX: {}({}pts)".format(self.SINGLE.POSITION, self.SINGLE.POINT, self.DOUBLE.POSITION, self.DOUBLE.POINT, self.MX.POSITION, self.MX.POINT)
        elif self.GENDER=='W':
            str+=" WS: {}({}pts), WD: {}({}pts), MX: {}({}pts)".format(self.SINGLE.POSITION, self.SINGLE.POINT, self.DOUBLE.POSITION, self.DOUBLE.POINT, self.MX.POSITION, self.MX.POINT)
        return str


class Serializer:
    def serialize(self): raise NotImplementedError()


class SerializerJson(Serializer):
    def serialize(self,data): return json.dumps(data)


class SerializerProtobuf(Serializer):
    def serialize(self,data): 
        player=player_pb2.Player()
        player.name=data["name"]
        player.licence=data["licence"]
        player.woman=data["gender"] == 'W'
        single=player.results.add()
        single.sport='single'
        single.points=data["single"]["point"]
        single.position=data["single"]["rank"]
        double=player.results.add()
        double.sport='double'
        double.points=data["double"]["point"]
        double.position=data["double"]["rank"]
        mx=player.results.add()
        mx.sport='mx'
        mx.points=data["mx"]["point"]
        mx.position=data["mx"]["rank"]
        return b64encode(player.SerializeToString())


async def outputStdout(loop,ranking, keyRanking='ALL', param=None):
    discList=[]
    if keyRanking == 'ALL':
      discList=['WS','MS','WD','MD','MM','MW']
    else:
      discList=[keyRanking]

    if 'MS' in discList:
      logger.info("Men's single {}".format(ranking['COLLECT']))
      logger.info("{0:5s} {1:10s} {2}[{3}]".format('rank','points','name','licence'))
      p=ranking['MS']
      while p is not None:
        logger.info("{0:5d}. {1:10s} {2}[{3}] ".format(p.PLAYER.SINGLE.POSITION,p.PLAYER.SINGLE.POINT,p.PLAYER.FULLNAME,p.PLAYER.LICENCE))
        p=p.nextSingle

    if 'WS' in discList:
      logger.info("Women's single {}".format(ranking['COLLECT']))
      logger.info("{0:5s} {1:10s} {2}[{3}]".format('rank','points','name','licence'))
      p=ranking['WS']
      while p is not None:
        logger.info("{0:5d}. {1:10s} {2}[{3}] ".format(p.PLAYER.SINGLE.POSITION,p.PLAYER.SINGLE.POINT,p.PLAYER.FULLNAME,p.PLAYER.LICENCE))
        p=p.nextSingle

    if 'MD' in discList:
      logger.info("Men's double {}".format(ranking['COLLECT']))
      logger.info("{0:5s} {1:10s} {2}[{3}]".format('rank','points','name','licence'))
      p=ranking['MD']
      while p is not None:
        logger.info("{0:5d}. {1:10s} {2}[{3}] ".format(p.PLAYER.DOUBLE.POSITION,p.PLAYER.DOUBLE.POINT,p.PLAYER.FULLNAME,p.PLAYER.LICENCE))
        p=p.nextDouble

    if 'WD' in discList:
      logger.info("Women's double {}".format(ranking['COLLECT']))
      logger.info("{0:5s} {1:10s} {2}[{3}]".format('rank','points','name','licence'))
      p=ranking['WD']
      while p is not None:
        logger.info("{0:5d}. {1:10s} {2}[{3}] ".format(p.PLAYER.DOUBLE.POSITION,p.PLAYER.DOUBLE.POINT,p.PLAYER.FULLNAME,p.PLAYER.LICENCE))
        p=p.nextDouble

    if 'MM' in discList:
      logger.info("Mixed double - Men {}".format(ranking['COLLECT']))
      logger.info("{0:5s} {1:10s} {2}[{3}]".format('rank','points','name','licence'))
      p=ranking['MM']
      while p is not None:
        logger.info("{0:5d}. {1:10s} {2}[{3}] ".format(p.PLAYER.MX.POSITION,p.PLAYER.MX.POINT,p.PLAYER.FULLNAME,p.PLAYER.LICENCE))
        p=p.nextMixed

    if 'MW' in discList:
      logger.info("Mixed double - Women {}".format(ranking['COLLECT']))
      logger.info("{0:5s} {1:10s} {2}[{3}]".format('rank','points','name','licence'))
      p=ranking['MW']
      while p is not None:
        logger.info("{0:5d}. {1:10s} {2}[{3}] ".format(p.PLAYER.MX.POSITION,p.PLAYER.MX.POINT,p.PLAYER.FULLNAME,p.PLAYER.LICENCE))
        p=p.nextMixed


async def outputSlack(loop,ranking, keyRanking='ALL', param=None):
    discList=[]
    if keyRanking == 'ALL':
      discList=['WS','MS','WD','MD','MM','MW']
    else:
      discList=[keyRanking]

    if 'MS' in discList:
        p=ranking['MS']
        msg="# men's single {}:".format(ranking['COLLECT'])
        while p is not None:
            msg+="\n{0:5d}. {1}[{2}] ({3})".format(p.PLAYER.SINGLE.POSITION, p.PLAYER.FULLNAME, p.PLAYER.LICENCE,p.PLAYER.SINGLE.POINT)
            p=p.nextSingle
        json_msg={"text": msg}
        async with aiohttp.ClientSession() as session:
          await session.post(param['url'], json=json_msg)

    if 'WS' in discList:
        p=ranking['WS']
        msg="# women's single {}:".format(ranking['COLLECT'])
        while p is not None:
          msg+="\n{0:5d}. {1}[{2}] ({3})".format(p.PLAYER.SINGLE.POSITION, p.PLAYER.FULLNAME, p.PLAYER.LICENCE,p.PLAYER.SINGLE.POINT)
          p=p.nextSingle
        json_msg={"text": msg}
        async with aiohttp.ClientSession() as session:
          await session.post(param['url'], json=json_msg)

    if 'WD' in discList:
        p=ranking['WD']
        msg="# women's double {}:".format(ranking['COLLECT'])
        while p is not None:
          msg+="\n{0:5d}. {1}[{2}] ({3})".format(p.PLAYER.DOUBLE.POSITION, p.PLAYER.FULLNAME, p.PLAYER.LICENCE,p.PLAYER.DOUBLE.POINT)
          p=p.nextDouble
        json_msg={"text": msg}
        async with aiohttp.ClientSession() as session:
          await session.post(param['url'], json=json_msg)

    if 'MD' in discList:
        p=ranking['MD']
        msg="# men's double {}:".format(ranking['COLLECT'])
        while p is not None:
          msg+="\n{0:5d}. {1}[{2}] ({3})".format(p.PLAYER.DOUBLE.POSITION, p.PLAYER.FULLNAME, p.PLAYER.LICENCE,p.PLAYER.DOUBLE.POINT)
          p=p.nextDouble
        json_msg={"text": msg}
        async with aiohttp.ClientSession() as session:
          await session.post(param['url'], json=json_msg)

    if 'MW' in discList:
        p=ranking['MW']
        msg="# mixed double women {}:".format(ranking['COLLECT'])
        while p is not None:
          msg+="\n{0:5d}. {1}[{2}] ({3})".format(p.PLAYER.MX.POSITION, p.PLAYER.FULLNAME, p.PLAYER.LICENCE,p.PLAYER.DOUBLE.POINT)
          p=p.nextMixed
        json_msg={"text": msg}
        async with aiohttp.ClientSession() as session:
          await session.post(param['url'], json=json_msg)

    if 'MM' in discList:
        p=ranking['MM']
        msg="# mixed double men {}:".format(ranking['COLLECT'])
        while p is not None:
          msg+="\n{0:5d}. {1}[{2}] ({3})".format(p.PLAYER.MX.POSITION, p.PLAYER.FULLNAME, p.PLAYER.LICENCE,p.PLAYER.DOUBLE.POINT)
          p=p.nextMixed
        json_msg={"text": msg}
        async with aiohttp.ClientSession() as session:
          await session.post(param['url'], json=json_msg)

async def outputSQS(loop,ranking, param=None):
    pre_headers = {'content-type': 'application/x-www-form-urlencoded'}
    query = {}

    aws_access_key=''
    secret_access_key=''
    with param['access'].open(mode='r') as ptr:
        aws_access_key=ptr.read().replace('\n','')
    with param['secret'].open(mode='r') as ptr:
        aws_secret_access_key=ptr.read().replace('\n','')
    passwd=None
    if param['encryption']:
        with param['encryption'].open(mode='r') as ptr:
            passwd=ptr.read().replace('\n','')

    mattr=None
    if 'sqsmattr' in param:
        mattrTab=param['sqsmattr'].split(':')
        mattr=[{'name': mattrTab[0], 'type': mattrTab[1], 'value': mattrTab[2]}]

    p=ranking['ALL']
    async with aiohttp.ClientSession() as session:
        sqsgw=aiosqs.SQS(aws_access_key, aws_secret_access_key, param['region'], param['host'],  param['endpoint'])
        while p is not None:
            player=p.PLAYER
            data=param['serializer'].serialize({
                'name': player.FULLNAME,
                'licence': player.LICENCE,
                'gender': player.GENDER,
                'single': { 'point':  float(player.SINGLE.POINT), 'rank': int(player.SINGLE.POSITION) },
                'double': { 'point':  float(player.DOUBLE.POINT), 'rank': int(player.DOUBLE.POSITION) },
                'mx': { 'point':  float(player.MX.POINT), 'rank': int(player.MX.POSITION) }
            })
            if passwd:
                await sqsgw.put(b64encode(encrypt(passwd,data)), session)
            else:
                await sqsgw.put(data, session, attrList=mattr)
            p=p.nextPlayer


async def outputSQSBatch(loop,ranking, param=None):
    #########################################################################
    #https://sqs.us-east-2.amazonaws.com/123456789012/MyQueue/
    #?Action=SendMessageBatch
    #&SendMessageBatchRequestEntry.1.Id=test_msg_001
    #&SendMessageBatchRequestEntry.1.MessageBody=test%20message%20body%201
    #&SendMessageBatchRequestEntry.2.Id=test_msg_002
    #&SendMessageBatchRequestEntry.2.MessageBody=test%20message%20body%202
    #&SendMessageBatchRequestEntry.2.DelaySeconds=60
    #&SendMessageBatchRequestEntry.2.MessageAttribute.1.Name=test_attribute_name_1
    #&SendMessageBatchRequestEntry.2.MessageAttribute.1.Value.StringValue=test_attribute_value_1
    #&SendMessageBatchRequestEntry.2.MessageAttribute.1.Value.DataType=String
    #&Expires=2020-05-05T22%3A52%3A43PST
    #&Version=2012-11-05
    #&AUTHPARAMS
    #########################################################################

    headers = {'content-type': 'application/x-www-form-urlencoded'}
    postData={"Action": "SendMessageBatch"}

    p=ranking['ALL']
    id=1 #needed by SQS
    while p is not None:
        player=p.PLAYER
        postData["SendMessageBatchRequestEntry.{}.Id".format(id)]=player.LICENCE
        postData["SendMessageBatchRequestEntry.{}.MessageBody".format(id)]=json.dumps({'name': player.FULLNAME, 'licence': player.LICENCE, 'gender': player.GENDER})
        #postData["SendMessageBatchRequestEntry.{}.MessageAttribute.1.Name".format(id)]="name"
        #postData["SendMessageBatchRequestEntry.{}.MessageAttribute.1.Value.StringValue".format(id)]=player.FULLNAME
        #postData["SendMessageBatchRequestEntry.{}.MessageAttribute.1.Value.DataType".format(id)]="String"
        #postData["SendMessageBatchRequestEntry.{}.MessageAttribute.2.Name".format(id)]="gender"
        #postData["SendMessageBatchRequestEntry.{}.MessageAttribute.2.Value.StringValue".format(id)]=player.GENDER
        #postData["SendMessageBatchRequestEntry.{}.MessageAttribute.2.Value.DataType".format(id)]="String"
        #postData["SendMessageBatchRequestEntry.{}.MessageAttribute.3.Name".format(id)]="singlept"
        #postData["SendMessageBatchRequestEntry.{}.MessageAttribute.3.Value.StringValue".format(id)]=player.SINGLE.POINT
        #postData["SendMessageBatchRequestEntry.{}.MessageAttribute.3.Value.DataType".format(id)]="Number"
        #postData["SendMessageBatchRequestEntry.{}.MessageAttribute.4.Name".format(id)]="singlerk"
        #postData["SendMessageBatchRequestEntry.{}.MessageAttribute.4.Value.StringValue".format(id)]=player.SINGLE.POSITION
        #postData["SendMessageBatchRequestEntry.{}.MessageAttribute.4.Value.DataType".format(id)]="Number"
        #postData["SendMessageBatchRequestEntry.{}.MessageAttribute.5.Name".format(id)]="doublept"
        #postData["SendMessageBatchRequestEntry.{}.MessageAttribute.5.Value.StringValue".format(id)]=player.DOUBLE.POINT
        #postData["SendMessageBatchRequestEntry.{}.MessageAttribute.5.Value.DataType".format(id)]="Number"
        #postData["SendMessageBatchRequestEntry.{}.MessageAttribute.6.Name".format(id)]="doublerk"
        #postData["SendMessageBatchRequestEntry.{}.MessageAttribute.6.Value.StringValue".format(id)]=player.DOUBLE.POSITION
        #postData["SendMessageBatchRequestEntry.{}.MessageAttribute.6.Value.DataType".format(id)]="Number"
        #postData["SendMessageBatchRequestEntry.{}.MessageAttribute.7.Name".format(id)]="mxpt"
        #postData["SendMessageBatchRequestEntry.{}.MessageAttribute.7.Value.StringValue".format(id)]=player.MX.POINT
        #postData["SendMessageBatchRequestEntry.{}.MessageAttribute.7.Value.DataType".format(id)]="Number"
        #postData["SendMessageBatchRequestEntry.{}.MessageAttribute.8.Name".format(id)]="mxrk"
        #postData["SendMessageBatchRequestEntry.{}.MessageAttribute.8.Value.StringValue".format(id)]=player.MX.POSITION
        #postData["SendMessageBatchRequestEntry.{}.MessageAttribute.8.Value.DataType".format(id)]="Number"
        id+=1
        p=p.nextPlayer

    print(postData)
    async with aiohttp.ClientSession(loop=loop) as session:
        await session.post(param['endpoint'], headers=headers, data=postData)


def updateRanking(playerWrap,chain,sortKey):
    if chain is None:
        return playerWrap

    p=chain
    pp=None
    if sortKey=='SINGLE':
        while p is not None:
            if p.PLAYER.SINGLE.POSITION >= playerWrap.PLAYER.SINGLE.POSITION:
                playerWrap.nextSingle=p
                if pp is None:
                    return playerWrap
                pp.nextSingle=playerWrap
                return chain
            else:
                pp=p
                p=p.nextSingle
        pp.nextSingle=playerWrap
        return chain

    elif sortKey=='DOUBLE':
        while p is not None:
            if p.PLAYER.DOUBLE.POSITION >= playerWrap.PLAYER.DOUBLE.POSITION:
                playerWrap.nextDouble=p
                if pp is None:
                    return playerWrap
                pp.nextDouble=playerWrap
                return chain
            else:
                pp=p
                p=p.nextDouble
        pp.nextDouble=playerWrap
        return chain

    elif sortKey=='MIXED':
        while p is not None:
            if p.PLAYER.MX.POSITION >= playerWrap.PLAYER.MX.POSITION:
                playerWrap.nextMixed=p
                if pp is None:
                    return playerWrap
                pp.nextMixed=playerWrap
                return chain
            else:
                pp=p
                p=p.nextMixed
        pp.nextMixed=playerWrap
        return chain

    else:
        raise KeyError("sortKey should be SINGLE,DOUBLE or MIXED but recieved {}".format(sortKey))


def hasError(playerChain):
    if playerChain.PLAYER.FULLNAME == '':
        playerChain.PLAYER.ERRORMSG="no name found"
        return True
    if playerChain.PLAYER.GENDER == '':
        playerChain.PLAYER.ERRORMSG="no gender found"
        return True
    return False

def cleanPlayerList(playerChains):
    p=playerChains['ALL']
    pp=None
    while p is not None:
        if hasError(p):
            tmp=p
            # remove p from ALL chain
            if pp is None:
                playerChains['ALL']=tmp.nextPlayer
            else:
                pp.nextPlayer=tmp.nextPlayer
            p=tmp.nextPlayer
            
            # add p to ERR chain
            tmp.nextPlayer=playerChains['ERR']
            playerChains['ERR']=tmp
        else:
          pp=p
          p=p.nextPlayer


def sortPlayerList(playerChains):
    p=playerChains['ALL']
    while p is not None:
        if p.PLAYER.GENDER=='M':
            playerChains['MS']=updateRanking(p,playerChains['MS'],'SINGLE')
            playerChains['MD']=updateRanking(p,playerChains['MD'],'DOUBLE')
            playerChains['MM']=updateRanking(p,playerChains['MM'],'MIXED')
        elif p.PLAYER.GENDER=='W':
            playerChains['WS']=updateRanking(p,playerChains['WS'],'SINGLE')
            playerChains['WD']=updateRanking(p,playerChains['WD'],'DOUBLE')
            playerChains['MW']=updateRanking(p,playerChains['MW'],'MIXED')
        else:
            raise KeyError("gender should be M or W but recieved '{}' for player {}({})".format(p.PLAYER.GENDER,p.PLAYER.ID, p.PLAYER.FULLNAME))
        p=p.nextPlayer


def parseHTMLPlayer(soupTable,playerInfo):
    caption=soupTable.find('caption').get_text().lstrip().rstrip()
    if caption[0:14] != "Rangliste von ":
        raise ValueError('no ranking information found for player {}'.format(player.ID))

    # extract name and licence number
    tmp=caption[14:-1].split('(')
    playerInfo.FULLNAME=tmp[0]
    playerInfo.LICENCE=tmp[1]

    # extract ranking
    for tr in soupTable.find_all('tr'):
        tdList=tr.find_all('td')
        if len(tdList) > 0:
            if tdList[0].get_text() == "Men's singles":
                playerInfo.GENDER='M'
                playerInfo.SINGLE=RANK()
                playerInfo.SINGLE.POSITION=int(tdList[1].text)
                playerInfo.SINGLE.POINT=tdList[4].get_text()
            elif tdList[0].get_text() == "Men's doubles":
                playerInfo.GENDER='M'
                playerInfo.DOUBLE=RANK()
                playerInfo.DOUBLE.POSITION=int(tdList[1].text)
                playerInfo.DOUBLE.POINT=tdList[4].get_text()
            elif tdList[0].get_text() == "Mixed doubles - Men":
                playerInfo.GENDER='M'
                playerInfo.MX=RANK()
                playerInfo.MX.POSITION=int(tdList[1].text)
                playerInfo.MX.POINT=tdList[4].get_text()
            elif tdList[0].get_text() == "Women's singles":
                playerInfo.GENDER='W'
                playerInfo.SINGLE=RANK()
                playerInfo.SINGLE.POSITION=int(tdList[1].text)
                playerInfo.SINGLE.POINT=tdList[4].get_text()
            elif tdList[0].get_text() == "Women's doubles":
                playerInfo.GENDER='W'
                playerInfo.DOUBLE=RANK()
                playerInfo.DOUBLE.POSITION=int(tdList[1].text)
                playerInfo.DOUBLE.POINT=tdList[4].get_text()
            elif tdList[0].get_text() == "Mixed doubles - Women":
                playerInfo.GENDER='W'
                playerInfo.MX=RANK()
                playerInfo.MX.POSITION=int(tdList[1].text)
                playerInfo.MX.POINT=tdList[4].get_text()


def parseHTML(html,player):
    soup=BeautifulSoup(html,'html.parser')
    divContent = soup.find("div", {"id": "content"})

    collectionDate = divContent.find(class_='rankingdate').contents[0][1:-1]
    rulerList=divContent.find_all(class_='ruler')
    for ruler in rulerList:
        if ruler.name=='table':
            parseHTMLPlayer(ruler,player)
            return
    raise ValueError('no information in HTML file found for player {}'.format(player.ID))


async def getPlayerInfo(loop,url,player,session):
    html=None
    async with session.get(url) as response:
        html=await response.text()
    if html is not None:
        parseHTML(html, player)
    else:
        raise ValueError('no HTML file recieved for player {}'.format(player.ID))
       

async def getWeekId(url,session):
    html=None
    opt=None
    headers = {"Authorization": "Basic f'{cookie_value}'"}
    async with session.get(url,headers=headers) as response:
        html=await response.text()
        soup=BeautifulSoup(html,'html.parser')
        selectContent = soup.find("select", {"class": "publication"})
        opt=selectContent.find("option", {"selected": "selected"})
    if opt is None:
      raise ValueError('cannot find information for year'.format(IDYEAR_SWISSBADMINTON))
    weekid=opt.get('value')
    weektxt=opt.get_text().lstrip().rstrip()
    return (weekid,weektxt)


async def acceptCookies(httpSession):
    #"btnAcceptCookies=Yes,%20I%20accept&__EVENTTARGET=&__EVENTARGUMENT=&__VIEWSTATE=" 'https://www.swiss-badminton.ch/cookies/?returnurl=%2f'
#    postArgs="btnAcceptCookies=Yes,%20I%20accept&__EVENTTARGET=&__EVENTARGUMENT=&__VIEWSTATE="
    postArgs={
        "btnAcceptCookies": "Yes,%20I%20accept",
        "__EVENTTARGET": None,
        "__EVENTARGUMENT": None,
        "__VIEWSTATE": None
    }
    async with httpSession.post('{}/cookies/?returnurl=%2f'.format(URL_SWISSBADMINTON),data=postArgs) as response:
        if response.status != 200:
            raise Exception('connection errors')
    


def printCookies(session):
    cookies=session.cookie_jar.filter_cookies(URL_SWISSBADMINTON)
    for var in cookies:
      print("{}     =>      {}".format(var,cookies[var]))
 
async def controller(loop,playerChains,outputList):
    #async with aiohttp.ClientSession(loop=loop,connector=aiohttp.TCPConnector(ssl=False),cookie_jar=aiohttp.CookieJar()) as session:
    headers = {"Authorization": "Basic f'{cookie_value}'"}
    async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar(),headers=headers) as session:
        logger.info("accept cookies")
        await acceptCookies(session)


        logger.info("get current week id")
        weekId,weekTxt=await getWeekId('{}/category.aspx?rid={}&category=2792'.format(URL_SWISSBADMINTON_RANKING,RID),session) 

        try:
            int(weekId)
        except ValueError as e:
            raise ValueError("recieved weekid ({}) from swiss-badminton should be an int".format(weekId))
##        cptWeekTxt=datetime.datetime.today().strftime("%U-%Y")
##        if cptWeekTxt != weekTxt:
##          raise ValueError("recieved week {} but should be {}".format(weekTxt,cptWeekTxt))
        logger.info("week {} ({}) found".format(weekTxt, weekId))

        playerChains['COLLECT']=weekTxt


        logger.info("get player informations")
        tasks=[]
        p=playerChains['ALL']
        while p is not None:
            url='{}/player.aspx?id={}&player={}'.format(URL_SWISSBADMINTON_RANKING,weekId,p.PLAYER.ID)
            tasks.append(getPlayerInfo(loop,url,p.PLAYER,session))
            p=p.nextPlayer
        completed,pending=await asyncio.wait(tasks)
        cleanPlayerList(playerChains)

    if playerChains['ERR'] is not None:
      logger.info("Problems with following players:")
      p=playerChains['ERR']
      while p is not None:
        logger.info("{} ({}): {}".format(p.PLAYER.FULLNAME,p.PLAYER.ID,p.PLAYER.ERRORMSG))
        p=p.nextPlayer

    # third phase: sort result
    logger.info("sort results")
    sortPlayerList(playerChains)

    # forth phase: publish result
    logger.info("publish to {}".format(outputList))
    outputTasks=[]
    if 'syslog' in outputList.keys():
      outputTasks.append(outputStdout(loop,playerChains))
    if 'slack' in outputList.keys():
      outputTasks.append(outputSlack(loop,playerChains,'ALL',outputList['slack']))
    if 'sqs' in outputList.keys():
      outputTasks.append(outputSQS(loop,playerChains,outputList['sqs']))

    if len(outputTasks) > 0:
      completed,pending=await asyncio.wait(outputTasks)


if __name__ == '__main__':
    # setup logging
    logging.basicConfig(format='%(asctime)-15s %(message)s',level=logging.INFO)
    logger=logging.getLogger()

    # parameter parsing
    parser=argparse.ArgumentParser()
    parser.add_argument("--playerid",help="list of Swissbadminton player ip numbers comma separated")
    parser.add_argument("--slack", help="send ranking to slack. SLACK_WEBHOOK environment var has to be setted",action="store_true")
    parser.add_argument("--syslog", help="send ranking to syslog",action="store_true")
    parser.add_argument("--sqs", help="send ranking to an SQS instance")
    parser.add_argument("--sqsmattr", help="message attribute. Format: <attrName>:<attrType>:<value>")
    parser.add_argument("--sqspb", help="serialize value using protobuf", action="store_true")
    parser.add_argument("--aws-region", dest='awsRegion', help="AWS region")
    parser.add_argument("--aws-host", dest='awsHost', help="AWS host")
    parser.add_argument("--aws-access-key", dest='awsAccess', help="file containing the AWS access key", default="/tmp/.aws_access_key")
    parser.add_argument("--aws-secret-access-key", dest='awsSecret', help="file containing the AWS secret access key", default="/tmp/.aws_secret_access_key")
    parser.add_argument("--encryption", dest='encryptionFile', help="file containing the encryption key")
    args=parser.parse_args()

    outputList={}
    if args.slack:
      outputList["slack"]={'url': os.environ.get('SLACK_WEBHOOK')}
    if args.syslog:
      outputList["syslog"]={}
    if args.sqs:
      outputList["sqs"]={
          'endpoint': args.sqs,
          'access': Path(args.awsAccess).resolve(strict=True),
          'secret': Path(args.awsSecret).resolve(strict=True),
          'region': args.awsRegion,
          'host': args.awsHost
      }
      if args.sqspb:
        outputList["sqs"]["serializer"]=SerializerProtobuf()
      else:
        outputList["sqs"]["serializer"]=SerializerJson()
    
    if args.encryptionFile:
        encr=Path(args.encryptionFile).resolve(strict=True)
    else:
      encr=None
    for out in outputList:
      outputList[out]['encryption']=encr

    # initialize data structure
    playerChains={'COLLECT': None, 'ALL': None, 'MS': None, 'WS': None, 'MD': None, 'WD': None, 'MM': None, 'MW': None, 'ERR': None}
    playerIdList=args.playerid.split(',')
    for idPlayer in playerIdList:
        try:
            int(idPlayer)
            player_node=PLAYER_CHAIN()
            player_node.PLAYER=PLAYER()
            player_node.PLAYER.ID=idPlayer
            player_node.nextPlayer=playerChains['ALL']
            playerChains['ALL']=player_node
        except ValueError as e:
            msg="player id must be a comma separated list of number. Recieved: '{}'".format(args.playerid)
            logger.critical(msg)
            raise TypeError(msg)

    loop=asyncio.get_event_loop()
    try:
        loop.run_until_complete(controller(loop,playerChains,outputList))
    finally:
        loop.close()

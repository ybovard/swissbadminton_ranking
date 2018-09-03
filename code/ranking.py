import configparser
import asyncio
import aiohttp
import logging
from bs4 import BeautifulSoup
import argparse

#https://www.swiss-badminton.ch/ranking/player.aspx?id=18623&player=2836215

class WRAPPER_PLAYER():
    PLAYER=None
    nextSingle=None
    nextDouble=None
    nextMixed=None

class RANK():
    POSITION=0
    POINT=0

class PLAYER_RANKING():
    ID=0
    LICENCE=0
    COLLECT='01-1970'
    FULLNAME='Player Name'
    GENDER=''
    SINGLE=None
    DOUBLE=None
    MX=None


    def __str__(self):
        str="({}) {}[{}]:".format(self.COLLECT,self.FULLNAME,self.LICENCE)
        if self.GENDER=='M':
            str+=" MS: {}({}pts), HD: {}({}pts), MX: {}({}pts)".format(self.SINGLE.POSITION, self.SINGLE.POINT, self.DOUBLE.POSITION, self.DOUBLE.POINT, self.MX.POSITION, self.MX.POINT)
        elif self.GENDER=='W':
            str+=" WS: {}({}pts), WD: {}({}pts), MX: {}({}pts)".format(self.SINGLE.POSITION, self.SINGLE.POINT, self.DOUBLE.POSITION, self.DOUBLE.POINT, self.MX.POSITION, self.MX.POINT)
        return str


async def outputStdout(loop,ranking):
    for disc,chain in ranking.items():
        if disc == 'MS':
            logger.info("Men's single:")
            logger.info("{0:5s} {1:10s} {2}[{3}]".format('rank','points','name','licence'))
            p=chain
            while p is not None:
                logger.info("{0:5d}. {1:10s} {2}[{3}] ".format(p.PLAYER.SINGLE.POSITION,p.PLAYER.SINGLE.POINT,p.PLAYER.FULLNAME,p.PLAYER.LICENCE))
                p=p.nextSingle
        elif disc == 'WS':
            logger.info("Women's single:")
            logger.info("{0:5s} {1:10s} {2}[{3}]".format('rank','points','name','licence'))
            p=chain
            while p is not None:
                logger.info("{0:5d}. {1:10s} {2}[{3}] ".format(p.PLAYER.SINGLE.POSITION,p.PLAYER.SINGLE.POINT,p.PLAYER.FULLNAME,p.PLAYER.LICENCE))
                p=p.nextSingle
        elif disc == 'MD':
            logger.info("Men's double:")
            logger.info("{0:5s} {1:10s} {2}[{3}]".format('rank','points','name','licence'))
            p=chain
            while p is not None:
                logger.info("{0:5d}. {1:10s} {2}[{3}] ".format(p.PLAYER.DOUBLE.POSITION,p.PLAYER.DOUBLE.POINT,p.PLAYER.FULLNAME,p.PLAYER.LICENCE))
                p=p.nextSingle
        elif disc == 'WD':
            logger.info("Women's double:")
            logger.info("{0:5s} {1:10s} {2}[{3}]".format('rank','points','name','licence'))
            p=chain
            while p is not None:
                logger.info("{0:5d}. {1:10s} {2}[{3}] ".format(p.PLAYER.DOUBLE.POSITION,p.PLAYER.DOUBLE.POINT,p.PLAYER.FULLNAME,p.PLAYER.LICENCE))
                p=p.nextSingle
        elif disc == 'MM':
            logger.info("Mixed double - Men:")
            logger.info("{0:5s} {1:10s} {2}[{3}]".format('rank','points','name','licence'))
            p=chain
            while p is not None:
                logger.info("{0:5d}. {1:10s} {2}[{3}] ".format(p.PLAYER.MX.POSITION,p.PLAYER.MX.POINT,p.PLAYER.FULLNAME,p.PLAYER.LICENCE))
                p=p.nextSingle
        elif disc == 'MW':
            logger.info("Mixed double - Women:")
            logger.info("{0:5s} {1:10s} {2}[{3}]".format('rank','points','name','licence'))
            p=chain
            while p is not None:
                logger.info("{0:5d}. {1:10s} {2}[{3}] ".format(p.PLAYER.MX.POSITION,p.PLAYER.MX.POINT,p.PLAYER.FULLNAME,p.PLAYER.LICENCE))
                p=p.nextSingle
        else:
            raise KeyError("discipline can be MS,WS,MD,WD,MM,MW but recieved {}".format(disc))
    asyncio.wait(1)


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



def sortPlayerList(playerList):
    ranking={}
    ranking['MS']=None
    ranking['WS']=None
    ranking['MD']=None
    ranking['WD']=None
    ranking['MM']=None
    ranking['MW']=None

    for player in playerList:
        wp=WRAPPER_PLAYER()
        wp.PLAYER=player
        if player.GENDER=='M':
            ranking['MS']=updateRanking(wp,ranking['MS'],'SINGLE')
            ranking['MD']=updateRanking(wp,ranking['MD'],'DOUBLE')
            ranking['MM']=updateRanking(wp,ranking['MM'],'MIXED')
        elif player.GENDER=='W':
            ranking['WS']=updateRanking(wp,ranking['WS'],'SINGLE')
            ranking['WD']=updateRanking(wp,ranking['WD'],'DOUBLE')
            ranking['MW']=updateRanking(wp,ranking['MW'],'MIXED')
        else:
            raise KeyError("gender should be M or W but recieved {}".format(player.GENDER))
    return ranking


def parseHTMLPlayer(soupTable):
    caption=soupTable.find('caption').get_text().lstrip().rstrip()
    if caption[0:14] != "Rangliste von ":
        return None

    playerInfo=PLAYER_RANKING()

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

    return playerInfo


def parseHTML(html):
    soup=BeautifulSoup(html,'html.parser')
    divContent = soup.find("div", {"id": "content"})

    collectionDate = divContent.find(class_='rankingdate').contents[0][1:-1]
    rulerList=divContent.find_all(class_='ruler')
    for ruler in rulerList:
        if ruler.name=='table':
            playerInfo=parseHTMLPlayer(ruler)
            if playerInfo:
                playerInfo.COLLECT=collectionDate
                return playerInfo
    
    return None


async def getRanking(loop,url,playerid):
    html=None
    async with aiohttp.ClientSession(loop=loop,connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
        async with session.get(url) as response:
            html=await response.text()

    if html is None:
       playerInfo=PLAYER_RANKING()
       playerInfo.ID=playerid
       return (True,playerInfo)
    else:
       playerInfo=parseHTML(html)
       playerInfo.ID=playerid
       return (playerInfo==None, playerInfo)
       


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument("--config",help="configuration file")
    parser.add_argument("--playerid",help="list of Swissbadminton player ip numbers comma separated")
    args=parser.parse_args()

    if args.config is not None:
      configFile=args.config
    else:
      configFile='ranking.ini'

    config=configparser.ConfigParser()
    config.read(configFile)

    logging.basicConfig(format='%(asctime)-15s %(message)s',level=logging.INFO)
    logger=logging.getLogger()

    loop=asyncio.get_event_loop()

    tasks=[]
    for player in config['PLAYER_LIST']:
        url='{}&player={}'.format(config['WEBSITE']['url'],config['PLAYER_LIST'][player])
        tasks.append(asyncio.ensure_future(getRanking(loop,url,config['PLAYER_LIST'][player])))

    if args.playerid is not None:
        for player in args.playerid.split(','):
            url='{}&player={}'.format(config['WEBSITE']['url'],player)
            tasks.append(asyncio.ensure_future(getRanking(loop,url,player)))

    playerList=[]
    tasks_done, _ =loop.run_until_complete(asyncio.wait(tasks))
    for res in tasks_done:
        err,obj=res.result()
        if err:
          logger.warn("problem when collecting information for player id {}".format(obj.ID))
        else:
          playerList.append(obj)

    ranking=sortPlayerList(playerList)

    outputTasks=[]
    outputTasks=[
        asyncio.ensure_future(outputStdout(loop,ranking))
    ]
    tasks_done, _ =loop.run_until_complete(asyncio.wait(outputTasks))

    loop.close()

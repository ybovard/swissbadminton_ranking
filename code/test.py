import player_pb2

data={"name": "Philipp Schneider ", "licence": "60593", "woman": False, "single": {"pts": 882.0, "pos": 387}, "double": {"pts": 1000.0, "pos": 369}, "mx": {"pts": 667.0, "pos": 464}}

player=player_pb2.Player()
player.name=data["name"]
player.licence=data["licence"]
player.woman=data["woman"]
single=player.results.add()
single.sport='single'
single.points=data["single"]["pts"]
single.position=data["single"]["pos"]
double=player.results.add()
double.sport='double'
double.points=data["single"]["pts"]
double.position=data["single"]["pos"]
mx=player.results.add()
mx.sport='mx'
mx.points=data["single"]["pts"]
mx.position=data["single"]["pos"]
print(player.SerializeToString())

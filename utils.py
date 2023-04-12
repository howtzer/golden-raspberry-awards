import json
from sqlalchemy.ext.declarative import DeclarativeMeta

class AlchemyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj.__class__, DeclarativeMeta):
            fields = {}
            for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
                data = obj.__getattribute__(field)
                try:
                    json.dumps(data)
                    fields[field] = data
                except TypeError:
                    fields[field] = None
            return fields
        return json.JSONEncoder.default(self, obj)


def atualiza_segundo_valor(response, operacao):
    response[operacao][1]["interval"] = response[operacao][0]["interval"]
    response[operacao][1]["producer"] = response[operacao][0]["producer"]
    response[operacao][1]["previousWin"] = response[operacao][0]["previousWin"]
    response[operacao][1]["followingWin"] = response[operacao][0]["followingWin"]


def atualiza_response(response, indice, intervalo, operacao):
    response[operacao][indice]["interval"] = intervalo["intervalos"]["maxInterval"]
    response[operacao][indice]["producer"] = intervalo["produtor"]
    response[operacao][indice]["previousWin"] = intervalo["intervalos"]["maxIntervalRange"]["menorAno"]
    response[operacao][indice]["followingWin"] = intervalo["intervalos"]["maxIntervalRange"]["maiorAno"]



RESPONSE_GET = {
        "min": [
        {
            "producer": "",
            "interval": 0,
            "previousWin": 0,
            "followingWin": 0
         },
        {
            "producer": "",
            "interval": 0,
            "previousWin": 0,
            "followingWin": 0
         }
        ],
        "max": [
        {
            "producer": "",
            "interval": 0,
            "previousWin": 0,
            "followingWin": 0
         },
        {
            "producer": "",
            "interval": 0,
            "previousWin": 0,
            "followingWin": 0
         }
        ]
    }
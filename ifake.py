# Copyright 2022 Cartesi Pte. Ltd.
#
# SPDX-License-Identifier: Apache-2.0
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use
# this file except in compliance with the License. You may obtain a copy of the
# License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.

from os import environ
import traceback
import logging
import requests
import json



logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)

rollup_server = environ["ROLLUP_HTTP_SERVER_URL"]
logger.info(f"HTTP rollup_server url is {rollup_server}")

def hex2str(hex):
    """
    Decodes a hex string into a regular string
    """
    return bytes.fromhex(hex[2:]).decode("utf-8")

def str2hex(str):
    """
    Encodes a string as a hex string
    """
    return "0x" + str.encode("utf-8").hex()

def handle_advance(data):
    """
    An advance request may be processed as follows:

    1. A notice may be generated, if appropriate:

    response = requests.post(rollup_server + "/notice", json={"payload": data["payload"]})
    logger.info(f"Received notice status {response.status_code} body {response.content}")

    2. During processing, any exception must be handled accordingly:

    try:
        # Execute sensible operation
        op.execute(params)

    except Exception as e:
        # status must be "reject"
        status = "reject"
        msg = "Error executing operation"
        logger.error(msg)
        response = requests.post(rollup_server + "/report", json={"payload": str2hex(msg)})

    finally:
        # Close any resource, if necessary
        res.close()

    3. Finish processing

    return status
    """

    """
    The sample code from the Echo DApp simply generates a notice with the payload of the
    request and print some log messages.
    """

    logger.info(f"Received advance request data {data}")

    status = "accept"
    try:
        logger.info("Adding notice")
        payloadstr = hex2str(data["payload"])
        requisicao = json.loads(payloadstr)
        user = data['metadata']['msg_sender']
        adcionar_requisitor_em_reputacao(user)
        if(REPUTACAO[user] <= 0): return "reject"
        if("id_cardapio" in requisicao):
            adiciona_nome_restaurante(user, requisicao["id_cardapio"])
            nome_restaurante = NOMES_RESTAURANTES[user]
            if(nome_restaurante not in CARDAPIO):
                CARDAPIO[nome_restaurante] = {}
            for itens in requisicao["itens"]:
                CARDAPIO[nome_restaurante][itens] = requisicao["itens"][itens]
            # CARDAPIO[user][requisicao["id_cardapio"]] = requisicao["itens"]
        elif("id_pedido" in requisicao):
            if(user in NOMES_RESTAURANTES):
                cliente = requisicao["cliente"]
                id_pedido = requisicao["id_pedido"]
                nome_restaurante = NOMES_RESTAURANTES[user]
                if(cliente not in PEDIDOS[nome_restaurante]):
                    return "reject"
                if(0 > id_pedido or id_pedido >= len(PEDIDOS[nome_restaurante][cliente])):
                    return "reject"
                PEDIDOS[nome_restaurante][cliente][id_pedido]["status"] = requisicao["status"]
                if(requisicao["status"] == "entregue"):
                    timestamp = data['metadata']['timestamp']
                    PEDIDOS[nome_restaurante][cliente][id_pedido]["timestamp"] = timestamp
                    if(REPUTACAO[user] < 5.0):
                        REPUTACAO[user] += 0.1
            else:
                restaurante = requisicao["cliente"]
                id_pedido = requisicao["id_pedido"]
                if(restaurante not in PEDIDOS):
                    return "reject"
                if(user not in PEDIDOS[restaurante]):
                    return "reject"
                if(0 > id_pedido or id_pedido >= len(PEDIDOS[restaurante][user])):
                    return "reject"
                if(PEDIDOS[restaurante][user][id_pedido]["status"] == "entregue" and requisicao["status"] == "entregue"):
                    if(REPUTACAO[user] < 5.0):
                        REPUTACAO[user] += 0.1
                    fim_pedido(restaurante, user, id_pedido)
                elif(PEDIDOS[restaurante][user][id_pedido]["status"] == "entregue" and requisicao["status"] == "nao entregue"):
                    timestamp = data['metadata']['timestamp']
                    diferenca = timestamp - PEDIDOS[restaurante][user][id_pedido]["timestamp"]
                    if(diferenca < 86400):
                        REPUTACAO[restaurante] -= 0.5
                        PEDIDOS[restaurante][user][id_pedido]["status"] = "conflito"
                        REPUTACAO[user] -= 0.3
                    fim_pedido(restaurante, user, id_pedido)

            # pass
        else:
            nome_restaurante = requisicao["restaurante"]
            # restaurante_addr = NOMES_RESTAURANTES[nome_restaurante]

            if(nome_restaurante not in CARDAPIO):
                return "reject"
            if(nome_restaurante not in PEDIDOS):
                PEDIDOS[nome_restaurante] = {}
            if(user not in PEDIDOS[nome_restaurante]):
                PEDIDOS[nome_restaurante][user] = []
            PEDIDOS[nome_restaurante][user].append({"item":requisicao["itens"], "anotacao":requisicao["anotacao"], "status":"pendendte"})
            # PEDIDOS[restaurante_addr][user][-1]["status"] = "pendendte"
        # payloadstr = f"{user}:  {payloadstr.upper()}"

        # response = requests.post(rollup_server + "/notice", json={"payload": str2hex(payloadstr)})
        # logger.info(f"Received notice status {response.status_code} body {response.content}")

    except Exception as e:
        status = "reject"
        msg = f"Error processing data {data}\n{traceback.format_exc()}"
        logger.error(msg)
        response = requests.post(rollup_server + "/report", json={"payload": str2hex(msg)})
        logger.info(f"Received report status {response.status_code} body {response.content}")

    return status

def handle_inspect(data):
    logger.info(f"Received inspect request data {data}")
    logger.info("Adding report")
    payloadstr = hex2str(data["payload"]).lower()
    if(payloadstr== "cardapio"):
    # payloadstr = f"{data['metadata']['msg_sender']}:  {payloadstr.upper()}"
        response = requests.post(rollup_server + "/report", json={"payload": str2hex(json.dumps(CARDAPIO))})
    elif(payloadstr== "pedidos"):
        response = requests.post(rollup_server + "/report", json={"payload": str2hex(json.dumps(PEDIDOS))})
    else:
        response = requests.post(rollup_server + "/report", json={"payload": str2hex("Não entendi")})
    logger.info(f"Received report status {response.status_code}")
    return "accept"

# def ler_pedido(pedido):
    
#     return "Pedido do cliente"

def adcionar_requisitor_em_reputacao(sender):
    if(sender not in REPUTACAO):
        REPUTACAO[sender] = 5.0

def fim_pedido(restaurante, cliente, pedido_id):
    pedido = json.dumps(PEDIDOS[restaurante][cliente][pedido_id])

    response = requests.post(rollup_server + "/notice", json={"payload": str2hex(pedido)})
    logger.info(f"Received notice status {response.status_code} body {response.content}")
    PEDIDOS[restaurante][cliente].pop(pedido_id)

def adiciona_nome_restaurante(id, nome):
    if(id not in NOMES_RESTAURANTES):
        NOMES_RESTAURANTES[id] = nome
        NOMES_RESTAURANTES[nome] = id

NOMES_RESTAURANTES = {

}
    
NOMES_CLIENTES = {

}
"""
ID : NOME
"""
    

REPUTACAO = {}

CARDAPIO = {}
    # "restaurant1": {
    #     "item1" : 1,
    #     "item2" : 2,
    #     "item3" : 3,
    #     "item4" : 4,
    #     "item5" : 5,
    #     "item6" : 6,
    # },
    # "restaurant2": {
    #     "Abacate1" : 1,
    #     "Abacate2" : 2,
    #     "Abacate3" : 3,
    #     "Abacate4" : 4,
    #     "Abacate5" : 5,
    #     "Abacate6" : 6,
    # }

PEDIDOS = {}

"""
restaurante : {
    cliente : []
} 

"""


handlers = {
    "advance_state": handle_advance,
    "inspect_state": handle_inspect,
}

finish = {"status": "accept"}
rollup_address = None

while True:
    logger.info("Sending finish")
    response = requests.post(rollup_server + "/finish", json=finish)
    logger.info(f"Received finish status {response.status_code}")
    if response.status_code == 202:
        logger.info("No pending rollup request, trying again")
    else:
        rollup_request = response.json()
        data = rollup_request["data"]
        if "metadata" in data:
            metadata = data["metadata"]
            if metadata["epoch_index"] == 0 and metadata["input_index"] == 0:
                rollup_address = metadata["msg_sender"]
                logger.info(f"Captured rollup address: {rollup_address}")
                continue
        handler = handlers[rollup_request["request_type"]]
        finish["status"] = handler(rollup_request["data"])

# -*- coding: utf-8 -*-
"""
Created on Fri Nov 29 09:36:14 2019

@author: ALU
"""
import json
import websocket
import asyncio

URL = "ws://localhost:31278/ws"

FIND_DONGLE = json.dumps({
                    "type":{
                            "type": "request",
                            "target_type": "device",
                            "target_name": "dongle"
                    },
                     "name": None,
                     "contents": "find_dongle"
              })

CONNECT_DEVICE = json.dumps({
                    "type":{
                            "type": "setting",
                            "target_type": "device",
                            "target_name": "dongle"
                    },
                     "name": None,
                     "contents": {
                         "on_off": True,
                         "target_id": "STEEG_DG329018",
                         "ch_config": 0
                    }
                 })

DEVICE_INFO = json.dumps({
                    "type":{
                            "type": "request",
                            "target_type": "device",
                            "target_name": "device"
                    },
                     "name": None,
                     "contents": "device_info"
              })

RAWDATA_SETTING = json.dumps({
                    "type":{
                            "type": "request",
                            "target_type": "raw",
                            "target_name": "raw"
                    },
                     "name": None,
                     "contents":{
                         "enable" : True,
                         "chunk_size": 4
                     }
                  }) 

RAWDATA_REQUEST = json.dumps({
                    "type":{
                            "type": "request",
                            "target_type": "raw",
                            "target_name": "raw"
                    },
                     "name": None,
                     "contents":{
                         "requirement" : [
                          "enable", "sps_origin",
                          "ch_num", "chunk_size",
                          "ch_label"]
                     }
                  })

RAWDATA = json.dumps({
            "type":{
                    "type": "data",
                    "target_type": "raw",
                    "target_name": "raw"
            },
             "name": None,
             "contents":{
                 "requirement" : [
                         "eeg", "sync_tick"
                 ]
             }
          })

ws = websocket.create_connection(URL)  # construct the connection

ws.send(FIND_DONGLE)
result =  ws.recv()
print (result)

ws.send(CONNECT_DEVICE)
result =  ws.recv()
print (result)

ws.send(RAWDATA_SETTING)
result =  ws.recv()
print (result)

ws.send(RAWDATA_REQUEST)
result =  ws.recv()
print (result)

ws.send(RAWDATA)
result =  ws.recv()
print (result)

ws.close()

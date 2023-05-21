import json, os, sys, random
from typing import Any, List, Dict, Tuple

abs_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(abs_path, ".."))

from web3 import Web3, HTTPProvider, WebsocketProvider
from eth_account import Account
from config import Config

class Web3Connector(object):
    def __init__(self, contractAddress, RPC, WCRPC, PRIVATE_KEY, ABI):
        ADDRESS = Web3.toChecksumAddress(contractAddress)
        if RPC:
            self.w3 = Web3(HTTPProvider(RPC))
        elif WCRPC:
            self.w3 = Web3(WebsocketProvider(WCRPC))
        self.acct = self.w3.eth.account.privateKeyToAccount(PRIVATE_KEY)
        self.contract = self.w3.eth.contract(address=ADDRESS, abi=ABI)

    @staticmethod
    def user_to_address(user):
        return Web3.toChecksumAddress(user)
    
    @staticmethod
    def string_to_bytes32(string):
        return Web3.toBytes(hexstr=string)
    
    @staticmethod
    def to_text(bytes):
        return Web3.toText(bytes)
    
    @staticmethod
    def is_address_0(user):
        return user == "0x0000000000000000000000000000000000000000"

    def send(self, func):
        """send web3 request

        Args:
            func (str): _description_. 'funcName(params)'

        Returns:
            _type_: _description_
        """
        # while 1:
        nonce = self.w3.eth.getTransactionCount(self.acct.address)
        # print(action, nonce)
        try:
            # print(func)
            construct_txn = eval('self.contract.functions.{}'.format(func)).buildTransaction({
                'from': self.acct.address,
                'nonce': nonce,
                'gas': 30000000,
                'gasPrice': self.w3.toWei('0', 'gwei'),
            })
            signed = self.acct.signTransaction(construct_txn)
            tx_hash = self.w3.eth.sendRawTransaction(signed.rawTransaction)
            tx_receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)
            # print(tx_receipt)
            return {"hash": tx_hash.hex(), "result": tx_receipt}
        except Exception as e:
            print(func, "execute error:", str(e))
            # nonce += 1
            # if nonce >= 3:
            #     break
            return

    def transfer(self, func, amount):
        """send web3 request

        Args:
            func (str): _description_. 'funcName(params)'

        Returns:
            _type_: _description_
        """
        # while 1:
        nonce = self.w3.eth.getTransactionCount(self.acct.address)
        # print(action, nonce)
        try:
            construct_txn = eval('self.contract.functions.{}'.format(func)).buildTransaction({
                'from': self.acct.address,
                'nonce': nonce,
                'gas': 300000,
                'gasPrice': self.w3.toWei('21', 'gwei'),
                'value': int(amount),
            })
            signed = self.acct.signTransaction(construct_txn)
            tx_hash = self.w3.eth.sendRawTransaction(signed.rawTransaction)
            tx_receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)
            return {"hash": tx_hash.hex(), "result": tx_receipt}
        except Exception:
            # nonce += 1
            # if nonce >= 3:
                # break
            return

    def call(self, func1):
        # while 1:
        nonce = self.w3.eth.getTransactionCount(self.acct.address)
        try:
            func = 'self.contract.functions.{}'.format(func1)
            result = eval(func).call()
            return result
        except Exception:
            return
            # nonce += 1
            # if nonce >= 3:
            #     break

    def searchEvent(self, event, fromBlock=0):
        event = "self.contract.events.{}".format(event)
        event_result = eval(event).createFilter(fromBlock=fromBlock).get_all_entries()
        return event_result

def new_account():
    account = Account.create()
    private_key = account.key
    return private_key.hex()

class MUDConnector(object):
    def __init__(self, private_key: str, cfg: Config, loadComponents=True) -> None:
        self.config = cfg
        self.private_key = private_key
        self.world = self._connect(cfg.world_address, "World.json")
        self.wallet = self.world.acct.address
        self.player = eval(self.wallet)
        if loadComponents:
            component_registry = self.world.call("components()")
            self._component_registry = self._connect(component_registry, "IUint256Component.json")
            self.id_to_component = dict()
            self.components = {x["name"]: self._get_component(x["name"]) for x in cfg.mud_components}
            self.component_types = {x["name"]: x["types"] for x in cfg.mud_components}
        # system_registry = self.world.call("systems()")
        # self._system_registry = self._connect(system_registry, "IUint256Component.json")
        self.systems = {x: self._get_system(x) for x in cfg.mud_systems}
        self.block = 0

    def _connect(self, address: str, abi_name: str) -> Web3Connector:
        return Web3Connector(address, self.config.w3_RPC, self.config.w3_WSRPC, self.private_key, self._get_abi(os.path.join(abs_path, "..", "..", self.config.abi_dir, abi_name)))

    def _get_abi(self, path: str):
        abi = list()
        with open(path, 'r', encoding='utf-8') as abi_file:
            abi = json.loads(abi_file.read())["abi"]
        return json.dumps(abi, ensure_ascii=False)

    def _get_component(self, component: str) -> Web3Connector:
        component_id = eval(Web3.solidityKeccak(["string"], [f"component.{component}"]).hex())
        # print(component, component_id)
        address = self._component_registry.call(f"getEntitiesWithValue({component_id})")
        component_address = hex(address[0])
        if len(component_address) < 42:
            component_address = "0x"+"0"*(42-len(component_address))+component_address[2:]
        self.id_to_component[component_id] = component
        print("load Component:", component, component_address)
        return self._connect(component_address, f"{component}Component.json")

    def _get_system(self, system: str) -> Web3Connector:
        system_id = eval(Web3.solidityKeccak(["string"], [f"system.{system}"]).hex())
        system_address = self.world.call(f"getSystemAddress({system_id})")
        if len(system_address) < 42:
            system_address = "0x"+"0"*(42-len(system_address))+system_address[2:]
        # self.id_to_component[system_id] = f"system.{system}"
        print("load System:", system, system_address)
        return self._connect(system_address, f"{system}System.json")
    
    def send(self, system: str, param: str):
        """
        send("Move", "(1,1)")
        -> self.systems["Move"].send("executeTyped((1,1))")
        """
        self.systems[system].send(f"executeTyped({param})")
    
    def has(self, component: str, entityId: int) -> bool:
        """
        components["Encounter"].call(f"has({mud.player})")
        """
        return self.components[component].call(f"has({entityId})")

    def set(self, component: str, entityId: int, value: str):
        """
        components["Encounter"].call(f"set({mud.player})")
        """
        return self.components[component].send(f"set({entityId},{value})")

    def remove(self, component: str, entityId: int):
        """
        components["Encounter"].call(f"remove({mud.player})")
        """
        return self.components[component].send(f"remove({entityId})")
    
    def getValue(self, component: str, entityId: Any) -> Any:
        """
        components["Position"].call(f"getValue({mud.player})")
        """
        return self.components[component].call(f"getValue({entityId})")
    
    def getEntitiesWithValue(self, component: str, value: str) -> List[Any]:
        """
        components["Position"].call(f"getEntitiesWithValue((1,1))")
        """
        return self.components[component].call(f"getEntitiesWithValue({value})")
    
    def getEntities(self, component: str) -> List[Any]:
        return self.components[component].call(f"getEntities()")
    
    def get_map(self) -> Dict[int, Dict[int, int]]:
        import base64
        w, h, ts = self.getValue("MapConfig", "")
        # dict<x, dict<y, t>>
        ret_dict = dict()
        counter = 0
        ts = base64.b16encode(ts).decode()
        while ts:
            t = int(ts[:2])
            ts = ts[2:]
            x = counter % w
            y = counter // w
            if x not in ret_dict:
                ret_dict[x] = dict()
            ret_dict[x][y] = t
            counter += 1
        return ret_dict
        # print(ret_dict)

    def get_equipments(self) -> Dict[int, Any]:
        ret_dict = dict()
        items = self.getEntities("ItemMetadata")
        # print(items)
        for item in items:
            boundary = self.getValue("Boundary2D", item)
            metadata = self.getValue("ItemMetadata", item)
            tx, ty, bx, by = boundary
            n, t, f = metadata
            coords = list()
            for x in range(tx, bx+1):
                for y in range(ty, by+1):
                    coord = (x, y)
                    coords.append(coord)
            ret_dict[item] = {
                "coords": coords,
                "name": n,
                "type": t,
                "functions": f
            }
        return ret_dict
    
    # def get_entity(self) -> 
    def get_events(self) -> List[Dict[str, Any]]:
        sets = self.world.searchEvent("ComponentValueSet", self.block)
        removes = self.world.searchEvent("ComponentValueRemoved", self.block)
        actions = list()
        while sets or removes:
            s = None
            s_block = None
            if sets:
                s = sets[0]
                s_block = s['blockNumber']
            r = None
            r_block = None
            if removes:
                r = removes[0]
                r_block = r['blockNumber']
            if (r_block is None or (s_block is not None and s_block <= r_block)) and s:
                # solve s
                address = self.id_to_component.get(s['args']['componentId'])
                if address:
                    info = {
                        "action": "set",
                        "component_address": s['args']['component'],
                        "component_name": address,
                        "entity": s['args']['entity'],
                        "data": self.parse_data(self.component_types[address], s['args']['data']),
                    }
                    actions.append(info)
                sets = sets[1:]
                self.block = s_block
                continue
            elif r:
                # solve r
                address = self.id_to_component.get(r['args']['componentId'])
                if address:
                    info = {
                        "action": "remove",
                        "component_address": r['args']['component'],
                        "component_name": address,
                        "entity": r['args']['entity'],
                        # "data": self.parse_data(self.component_types[address], r['args']['data']),
                    }
                    actions.append(info)
                removes = removes[1:]
                self.block = r_block
                continue
            # print(s)
            # print(r)
            break
        return actions
    
    def parse_data(self, types: List[str], data: bytes) -> Tuple[Any]:
        # print(types, data)
        return self.world.w3.eth.codec.decode_abi(types, data)
    
    # def get_changes(self) -> 

if __name__ == "__main__":
    cfg = Config(os.path.join(abs_path, "..", "config", "app.json"))
    pk = "0x19c03c5470a3aa51075bbc069deda1c9c57be29fde0e3ae6e24c34ec687162a8"
    # # pk = "0x22a049545bcf647578b9f31de26310413516f735c2c44800e8eb695517d628f3"
    # # pk = new_account()
    # # print(pk)
    mud = MUDConnector(pk, cfg)
    # mud.send("Move", '(6,14)')
    print(mud.get_events())
    # for equipment, item in mud.get_equipments().items():
    #     if item["type"] == "Bed":
    #         print(item["name"], item["type"], item["functions"])
    #         print(item["coords"])
    # sets = mud.world.searchEvent("ComponentValueSet", 0)
    # removes = mud.world.searchEvent("ComponentValueRemoved", 0)
    # actions = list()
    # cur_block = 0
    # while sets or removes:
    #     s = None
    #     s_block = None
    #     if sets:
    #         s = sets[0]
    #         s_block = s['blockNumber']
    #     r = None
    #     r_block = None
    #     if removes:
    #         r = removes[0]
    #         r_block = r['blockNumber']
    #     if (r_block is None or (s_block is not None and s_block <= r_block)) and s:
    #         # solve s
    #         address = mud.id_to_component.get(s['args']['componentId'])
    #         if address:
    #             info = {
    #                 "action": "set",
    #                 "component_address": s['args']['component'],
    #                 "component_name": address,
    #                 "entity": s['args']['entity'],
    #                 "data": s['args']['data'],
    #             }
    #             actions.append(info)
    #         sets = sets[1:]
    #         cur_block = s_block
    #         continue
    #     elif r:
    #         # solve r
    #         address = mud.id_to_component.get(r['args']['componentId'])
    #         if address:
    #             info = {
    #                 "action": "remove",
    #                 "component_address": r['args']['component'],
    #                 "component_name": address,
    #                 "entity": r['args']['entity'],
    #                 "data": r['args']['data'],
    #             }
    #             actions.append(info)
    #         removes = removes[1:]
    #         cur_block = r_block
    #         continue
    #     # print(s)
    #     # print(r)
    #     break
    # actions = mud.get_events()
    # for action in actions:
    #     print(action)
        # if action["component_name"] == "component.ItemMetadata":
        #     print(mud.parse_data(["string", "string", "string"], action["data"]))
    # print(actions)
    # print(len(actions))
    # print(mud.getValue("MapConfig", ""))
    # print(mud.get_map())
    # print(new_account())
    # print(new_account())
    # print(new_account())
    # import base64
    # a = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00`\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xa0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0cschool class\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00@You can teach students with a school class if you are a teacher.\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00 \x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0eteach students\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    # print(mud.world.to_text(a))
    # print(eval(a.decode()))
    # b = base64.b16encode(a)
    # print(b.decode())
    # print(mud.components["Position"].call(f"getEntitiesWithValue((1,1))"))
    # cur_position = mud.components["Position"].call(f"getValue({mud.player})")
    # print("current position:", cur_position)
    # # print("(1, 1):", entities)
    # print(mud.systems['JoinGame'].send(f"executeTyped((1,1))"))
    # print(mud.components["Position"].call(f"getEntitiesWithValue((1,1))"))
    # targets = [
    #     [-1, 0],
    #     [0, -1],
    #     [1, 0],
    #     [0, 1]
    # ]
    # for _ in range(10):
        # cur_position = mud.components["Position"].call(f"getValue({mud.player})")
        # print("current position:", cur_position)
        # movable = mud.components["Movable"].call(f"has({mud.player})")
        # if not movable:
        #     print("cannot move!")
        #     break
        # encounter = mud.components["Encounter"].call(f"has({mud.player})")
        # if encounter:
        #     print("encounter!")
        #     break
        # choices = [x for x in range(len(targets))]
        # while choices:
        #     choice = random.choice(choices)
        #     new_position = tuple([cur_position[0] + targets[choice][0], cur_position[1] + targets[choice][1]])
        #     print("position:", new_position)
        #     choices.remove(choice)
        #     entities = mud.components["Position"].call(f"getEntitiesWithValue(({new_position[0]},{new_position[1]}))")
        #     if entities:
        #         print("have entity")
        #         continue
        #     hash_value = mud.systems["Move"].send(f"executeTyped(({new_position[0]},{new_position[1]}))")['hash']
        #     print(mud.world.w3.eth.getTransaction(hash_value))
        #     print("choice:", choice)
        #     break

    # print(mud.components["Position"].call(f"getValue({mud.player})"))
    # abi_dir = r"D:\WorkSpace\ShareWithUbuntu2204\llm-town\contracts\abi"
    # wsrpc = "ws://43.163.220.70:8545"
    # rpc = None # "http://43.163.220.70:8545"
    # private_key = "0x86a80a3f189c23bc7fa7b2efad60572a4e72c0d90ae3d2e5ae08f4bdb4727bf0"
    # world_address = "0x7B4f352Cd40114f12e82fC675b5BA8C7582FC513"
    # world = Web3Connector(world_address, rpc, wsrpc, private_key, get_abi(os.path.join(abi_dir, "World.json")))
    # component_registry = world.call("components()")
    # components = Web3Connector(component_registry, rpc, wsrpc, private_key, get_abi(os.path.join(abi_dir, "IUint256Component.json")))
    # position_id = eval(Web3.solidityKeccak(["string"], ["component.Position"]).hex())
    # res = components.call(f"getEntitiesWithValue({position_id})")
    # position_address = hex(res[0])
    # position = Web3Connector(position_address, rpc, wsrpc, private_key, get_abi(os.path.join(abi_dir, "PositionComponent.json")))
    # # left/right: x  up/down: y
    # # print(position.call(f"getEntitiesWithValue((0,0))"))
    # # print(position.call(f"getEntitiesWithValue((0,1))"))
    # # print(position.call(f"getEntitiesWithValue((1,0))"))
    # # print(position.call(f"getEntitiesWithValue((1,1))"))
    # for x in position.call(f"getEntities()"):
    #     if x == eval(position.acct.address):
    #         print(x, position.call(f"getValue({x})"))
    #     # print(hex(x))
    #     # if hex(x) == hex(997949618850540162853569413447729110388758399019):
    #         # print("equels")
    # # print(hex(997949618850540162853569413447729110388758399019))
    # # 0x8b190573374637f144ac8d37375d97fd84cbd3a0
    # # 0x7B4f352Cd40114f12e82fC675b5BA8C7582FC513
    # # componentId = world.call(f"getComponentIdFromAddress('{component_registry}')")
    # # print(entity_count)
    # # for i in range(entity_count):
    # #     print(i, world.call(f"hasEntity({i})"))
    # #     if i > 5:
    # #         break
    # # print(i, world.call(f"hasEntity({i})"))
    # # print(componentId, world.call(f"hasEntity({componentId})"))
    # # componentAddress = world.call(f"getComponent({componentId})")
    # # print(componentAddress == component_registry)
    # # print(Web3.toText(hexstr="0x5a80b0e77cbf0fb68f4d0531656d7eaaa9d6f70a455916a21ade7ee809dfbd77"))
    # # res = components.call("")
    # print(new_account())

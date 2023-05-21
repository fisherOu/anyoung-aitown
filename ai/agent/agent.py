from typing import List, Dict, Any
import re
import json

from agent.memory.memory import Memory, Observation, Background, Plan, Reflection, BACKGROUND, OBSERVATION, PLAN, REFLECTION
from agent.memory.memory_stream import MemoryStream
from utils.gpt import GPTCaller
from utils.tools import timestamp_to_datetime, format_timestamp
from utils.w3 import MUDConnector, new_account
from config import AgentConfig

class Properties:
    def __init__(self, properties: Dict[str, Any]) -> None:
        self.properties = properties
        # for key, value in config.agent_properties.items():
        #     self.properties[key] = properties[key] if key in properties else value

    def get_property(self, key: str) -> Any:
        return self.properties[key]
    
    def set_property(self, key: str, value: Any):
        self.properties[key] = value

    def to_json(self) -> Dict[str, Any]:
        return self.properties

class Agent:
    def __init__(self, gpt: GPTCaller, config: AgentConfig, app) -> None:  # , properties: Dict[str, Any]
        self.gpt = gpt
        self.app = app
        self.config = config
        self.memory_stream = MemoryStream()
        self.properties =  Properties(config.agent_properties)
        self.background_stored = False
        self._init_mud()
        if not self.app.entities.get(self.mud.player, dict()).get("Status"):
            self.mud.send("Status", '"Wandering"')
        self.move_path = list()
        self.timer = dict()
        self.action = ""
        self.status = "Wandering"
        self.next_operation = ""
        self.plan = "no plan yet"
        self.emotion = ""
        self.language = ""
        self.languages = list()
        # TODO: record last sight & save observation only when new equip or agent in sight
        self.last_sight = set()
        self.sight = dict()
        self.operation = {"choices": [], "operation": ""}
        self.memory_prompt = ""

    def react(self, observation: str, time_tick: int) -> Dict[str, Any]:
        """
        agent react with observation
        """
        operations = list()
        sight = dict()
        if not observation:
            sight = self._get_sight(time_tick)
            observation = sight["observation"]
            operations = sight["operations"]
            entities = sight["entities"]
            operation_dict = sight["operation_dict"]
            self.app.log("sight: "+str(sight))
            found = False
            for entity in entities:
                if entity not in self.last_sight:
                    found = True
                    break
            if (not found and len(entities) > 0) or (len(entities) == 0 and self.plan and self.memory_prompt):
                # old sight
                # if self.move_path and self.move_to(self.move_path[0][0], self.move_path[0][1]):
                #     self.move_path.pop(0)
                print(self.move_path)
                if len(self.move_path) == 0 and self.next_operation and self.sight.get("operation_dict", dict()).get(self.next_operation):
                    position = self.sight.get("operation_dict", dict()).get(self.next_operation)
                    entity = self.app.position.get(position[0], dict()).get(position[1])  # agent.mud.getEntitiesWithValue("Position", f"({position[0]},{position[1]})")
                    self.mud.send("Interaction", f'({entity},"{self.next_operation}")')
                    self.action = self.next_operation
                    self.next_operation = ""
                self.last_sight = entities
                self.sight = sight
                if "name" in self.operation:
                    del self.operation["name"]
                # if "name" in self.operation:
                #     del self.operation["name"]
                return {"status": self.status, "operation": self.operation, "sight": self.last_sight, "memory_prompt": self.memory_prompt, "plan": self.plan}
        # 用plan检索评价observation importance的记忆流
        related_person = self._parse_related_person(observation)
        prompt = Observation(observation, 0, self.get_state("location"), related_person, time_tick)
        # retrieve: get memory-list
        memory = self._retrieve(prompt, time_tick)
        # organize memory-prompt
        background_prompt = self.memory_stream.background.content
        memory_prompt = self._prompt(memory, prompt)
        self.app.log("memory_prompt: "+memory_prompt)
        # save observation
        prompt.importance = self._get_importance(background_prompt, memory_prompt, prompt, prompt.content, "observation")
        self.memory_stream.store_memory(prompt)
        # plan: get & save plan
        # 用plan+observation检索评价plan importance的记忆流
        plan = self._plan(background_prompt, memory_prompt, prompt, time_tick)
        self.app.log("plan: "+plan.content)
        self.memory_stream.store_memory(plan)
        # raise ValueError("stop here!")
        # act: get action
        # action = self._act(memory_prompt, prompt, time_tick)
        operation = {"choices": [], "operation": ""}
        if operations:
            operation = self._act(background_prompt, memory_prompt, prompt, plan.content, sight, time_tick)
            self.operation = operation
        self.memory_prompt = memory_prompt
        self.last_sight = entities
        self.sight = sight
        self.plan = plan.content
        return {"status": self.status, "operation": operation, "sight": sight, "memory_prompt": memory_prompt, "plan": plan.content, 'prompt': prompt.content}
    
    def speak(self, target: str, memory_prompt: str, prompt: str, time_tick: int) -> str:
        speak_prompt = self.config.speak_prompt
        speak_prompt = speak_prompt.replace("{target}", target)
        speak_prompt = self._replace_keyInfo(speak_prompt, memory_prompt, prompt, time_tick)
        return self._ask(memory_prompt, speak_prompt, self.config.act_model)

    def reflect(self, time_tick: int):
        """
        agent reflect memories
        """
        # reflect: get & save reflection
        memory = self.memory_stream.most_recent_memories(time_tick, self.config.reflect_time_diff)
        start_prompt = self.config.start_reflect_prompt
        start_prompt = start_prompt.replace("{time}", format_timestamp(time_tick))
        importance = self.config.reflect_importance
        prompt = Memory(start_prompt, importance, self.get_state("location"), [], OBSERVATION, time_tick)
        memory_prompt = self._prompt(memory, prompt)
        reflection = self._reflect(memory_prompt, prompt, time_tick)
        self.app.log("reflection: "+reflection.content)
        self.memory_stream.store_memory(reflection)

    def prompt(self, content: str, time_tick: int) -> Dict[str, Any]:
        prompt = Observation(content, 5, self.get_state("location"), [], time_tick)
        # retrieve: get memory-list
        memory = self._retrieve(prompt, time_tick)
        memory_prompt = self._prompt(memory, prompt)
        self.memory_stream.store_memory(prompt)
        plan = self._plan(memory_prompt, prompt, time_tick)
        self.memory_stream.store_memory(plan)
        return {"action": self.status, "operation": None, "sight": self.sight, "memory_prompt": memory_prompt, "plan": plan, 'prompt': prompt.content}

    def set_state(self, key: str, value: Any):
        """
        agent change location/name/etc.
        """
        self.properties.set_property(key, value)
    
    def get_state(self, key: str) -> Any:
        """
        agent get location/name/etc.
        """
        return self.properties.get_property(key)

    def store_background(self, time_tick: int):
        """
        agent init background memory.
        """
        if self.background_stored:
            return
        # agent
        content = self.config.background_prompt
        content = self._replace_keyInfo(content, "", None, time_tick)
        # locations
        # for location in self.app.locations.values():
        #     content += location.to_description()
        importance = self.config.background_importance
        background = Background(content, importance, self.get_state("location"), [], time_tick)
        self.memory_stream.store_memory(background)
        self.background_stored = True

    def get_plan(self) -> Plan:
        return self.memory_stream.plan

    def complete_plan(self):
        self.memory_stream.complete_plan()

    def _retrieve(self, prompt: Memory, time_tick: int) -> List[Memory]:
        return self.memory_stream.get_similar_memory(prompt, self.config.retrieve_params, time_tick)

    def _prompt(self, memories: List[Memory], origin_prompt: Memory) -> str:
        prompts = list()
        for memory in memories:
            prompt = self._transfer_prompt(memory, origin_prompt)
            if prompt:
                prompts.append(prompt)
        # prompt = self._transfer_prompt(origin_prompt, None)
        # if prompt:
        #     prompts.append(prompt)
        return "".join(prompts)

    def _plan(self, backgroud_prompt: str, memory_prompt: str, origin_prompt: Memory, time_tick: int) -> Memory:
        plan_prompt = self.config.plan_prompt
        plan_prompt = self._replace_keyInfo(plan_prompt, memory_prompt, origin_prompt, time_tick)
        plan_prompt = plan_prompt.replace("{plan}", self.plan)
        content = self._ask(backgroud_prompt, plan_prompt, self.config.reflect_model)
        plan_content = re.findall(r'{.*?}', content, re.DOTALL)
        if plan_content:
            plan_content = plan_content[0]
        else:
            plan_content = "{}"
        print("plan_content:", plan_content)
        plan_content = json.loads(plan_content).get("interaction", "")
        # raise ValueError(f"Plan: {plan_content[0]}")
        importance = self._get_importance(backgroud_prompt, memory_prompt, origin_prompt, plan_content, "plan")
        return Plan(plan_content, importance, self.get_state("location"), origin_prompt.related_person, time_tick)

    def _reflect(self, backgroud_prompt: str, memory_prompt: str, origin_prompt: Memory, time_tick: int) -> Memory:
        reflect_prompt = self.config.reflect_prompt
        reflect_prompt = self._replace_keyInfo(reflect_prompt, memory_prompt, origin_prompt, time_tick)
        content = self._ask(backgroud_prompt, reflect_prompt, self.config.reflect_model)
        importance = self._get_importance(backgroud_prompt, memory_prompt, origin_prompt, content, "reflection")
        return Reflection(content, importance, origin_prompt, self.get_state("location"), origin_prompt.related_person, time_tick)

    def _act(self, backgroud_prompt: str, memory_prompt: str, origin_prompt: Memory, plan: str, sight: Dict[str, Any], time_tick: int) -> Dict[str, Any]:
        act_prompt = self.config.act_prompt
        act_prompt = self._replace_keyInfo(act_prompt, memory_prompt, origin_prompt, time_tick)
        act_prompt = act_prompt.replace("{plan}", plan)
        # equipments = json.dumps(sight.get("equipments", dict()), ensure_ascii=False)
        equipments = list()
        interactions = list()
        for name, operations in sight.get("equipments", dict()).items():
            equipment = {
                "name": name,
                "interactions": operations
            }
            interactions.extend(operations)
            equipments.append(equipment)
        interactions.append("go to \'your chosen buildings\'")
        interactions.append("talk with nearby people")
        act_prompt = act_prompt.replace("{equipments}", json.dumps(equipments, ensure_ascii=False))
        act_prompt = act_prompt.replace("{operations}", json.dumps([x for x in set(interactions)], ensure_ascii=False))
        act_prompt = act_prompt.replace("{people}", json.dumps([x for x in sight.get("people", set())]))
        content = self._ask(backgroud_prompt, act_prompt, self.config.act_model)
        act_content = re.findall(r'{.*?}', content, re.DOTALL)
        if act_content:
            act_content = act_content[0]
        else:
            act_content = "{}"
        action = json.loads(act_content)
        return action
    
    def _operate(self, backgroud_prompt: str, memory_prompt: str, origin_prompt: Memory, content: str, operations: Dict[str, str], time_tick: int) -> str:
        operation_prompt = self.config.operation_prompt
        origin = self._transfer_prompt(origin_prompt, None)
        operation_prompt = operation_prompt.replace("{origin}", origin)
        operation_prompt = operation_prompt.replace("{content}", content)
        operation_prompt = operation_prompt.replace("{operations}", "".join(operations.values()))
        answer = self._ask(backgroud_prompt, operation_prompt, self.config.act_model)
        choices = list()
        for key in operations.keys():
            if key in answer:
                choices.append(key)
        return {"choices": choices, "operation": answer}

    def _ask(self, system: str, user: str, model: str) -> str:
        # self.app.log(f"system prompt: {system} and user prompt: {user} using model: {model}")
        return self.gpt.call(system, user, model)

    def _get_importance(self, background_prompt: str, memory_prompt: str, origin_prompt: Memory, content: str, source: str) -> int:
        origin = self._transfer_prompt(origin_prompt, None)
        importance_prompt = self.config.importance_prompt
        importance_prompt = importance_prompt.replace("{origin}", origin)
        importance_prompt = importance_prompt.replace("{memory}", memory_prompt)
        importance_prompt = importance_prompt.replace("{content}", content)
        importance_prompt = importance_prompt.replace("{source}", source)
        answer = self._ask(background_prompt, importance_prompt, self.config.importance_model)
        score = self._parse_importance_score(answer)
        return score

    def _parse_importance_score(self, answer: str) -> int:
        ints = re.findall(r"\d+", answer)
        if ints:
            return int(ints[0])
        else:
            return 0

    def _transfer_prompt(self, memory: Memory, origin_prompt: Memory) -> str:
        prompt = ""
        if memory.memory_type == BACKGROUND:
            prompt = memory.content
        elif memory.memory_type == OBSERVATION:
            prompt = memory.content
        elif memory.memory_type == PLAN:
            prompt = memory.content
        elif memory.memory_type == REFLECTION:
            prompt = memory.content
        return prompt
    
    def _parse_related_person(self, content: str) -> List[str]:
        friends = list()
        for friend in self.get_state("friends"):
            if friend in content:
                friends.append(friend)
        return friends

    def _replace_keyInfo(self, prompt_template: str, memory_prompt: str, prompt: Memory, time_tick: int) -> str:
        for key in self.config.prompt_replaces:
            if key not in prompt_template:
                continue
            if key.startswith("{target"):
                if prompt is not None:
                    if key == "{target_name}":
                        prompt_template = prompt_template.replace(key, ",".join(prompt.related_person))
                    if key == "{target_location}":
                        prompt_template = prompt_template.replace(key, prompt.location)
                    if key == "{target_time}":
                        prompt_template = prompt_template.replace(key, format_timestamp(prompt.created))
                    if key == "{target_content}":
                        prompt_template = prompt_template.replace(key, prompt.content)
                else:
                    prompt_template = prompt_template.replace(key, "")
            elif key == "{time}":
                prompt_template = prompt_template.replace(key, format_timestamp(time_tick))
            elif key == "{locations}":
                prompt_template = prompt_template.replace(key, json.dumps([x for x in self.app.locations.keys()], ensure_ascii=False))
            elif key == "{memory}":
                prompt_template = prompt_template.replace(key, memory_prompt)
            # elif key == "{friendship}":
            #     prompt_template = prompt_template.replace(key, ",".join(prompt.related_person))
            else:
                prompt_template = prompt_template.replace(key, self.properties.get_property(key[1:-1]))
        return prompt_template
    
    def _init_mud(self):
        self.mud = MUDConnector(self.config.private_key, self.app.config, False)
        # if self.mud.getValue("Position", f"{self.mud.player}"):
        #     return
        # print(self.app.entities[self.mud.player].get("Position"))
        # print(self.app.entities[self.mud.player].get("Agent"))
        # print(self.app.entities[self.mud.player].get("Status"))
        if self.mud.player in self.app.entities and self.app.entities[self.mud.player].get("Position"):
            return
        # if self.mud.has("Player", f"{self.mud.player}"):
        #     return
        found = False
        for x in range(self.app.width):
            for y in range(self.app.height):
                if self.app.position.get(x, dict()).get(y):
                    continue
                found = True
                self.mud.send("Agent", f'("{self.get_state("name")}",{self.get_state("age")},"{self.get_state("career")}","{self.get_state("model")}")')
                self.mud.send("JoinGame", f'({x},{y})')
                self.mud.send("Status", '"Wandering"')
                break
            if found:
                break

    def distance(self, coord1: tuple, coord2: tuple) -> int:
        return abs(coord2[0]-coord1[0])+abs(coord2[1]-coord1[1])

    def _get_sight(self, time_tick: int) -> Dict[str, Any]:
        cur_position = self.app.entities.get(self.mud.player, dict()).get("Position")  # self.app.entities.get(self.mud.player, dict()).get("Position") # self.mud.getValue("Position", self.mud.player)
        if not cur_position:
            return
        cur_position = cur_position[0]
        sight = list()
        sight.append(f"current time is: {format_timestamp(time_tick)}.")
        operations = dict()
        operation_dict = dict()
        entities = set()
        people = set()
        equipments = dict()
        # get l r t b
        left = max(0, cur_position[0] - self.config.sight)
        right = min(self.app.width, cur_position[0] + self.config.sight)
        top = max(0, cur_position[1] - self.config.sight)
        bottom = min(self.app.height, cur_position[1] + self.config.sight)
        for x in range(left, right):
            for y in range(top, bottom):
                if x == cur_position[0] and y == cur_position[1]:
                    # TODO: get current location and set_state("location")
                    for location, Location in self.app.locations.items():
                        range_value = Location.get_state("range")
                        if range_value and range_value[0] <= x <= range_value[2] and range_value[1] <= y <= range_value[3]:
                            self.set_state("location", location)
                    continue
                prompt = ""
                # if self.app.map[x][y] > 0:
                #     terrain = self.app.get_terrain_config(self.app.map[x][y])
                #     sub_prompt = self.config.terrain_prompt
                #     # prompt = prompt.replace("{name}", terrain.name)
                #     sub_prompt = sub_prompt.replace("{passable}", "able" if terrain.passable else "unable")
                #     prompt += sub_prompt
                #     self.app.log("get_sight-block: "+sub_prompt)
                if self.app.coord2equipment.get(x, dict()).get(y):
                    # equipment
                    equipment = self.app.equipments[self.app.coord2equipment.get(x, dict()).get(y)]
                    name = equipment["type"]
                    if name not in entities:
                        entities.add(name)
                        if equipment.get("config"):
                            # prompt += equipment["config"].description
                            self.app.log("get_sight-equipment: "+equipment["config"].description)
                            if equipment["config"].operations:
                                equipments[name] = list()
                                for operation in equipment["config"].operations:
                                    # if self.distance(cur_position, (x, y)) > operation["distance"]:
                                    #     continue
                                    if operation["name"] not in operations:
                                        equipment_operation = self.config.equipment_operation
                                        equipment_operation = equipment_operation.replace("{name}", equipment["config"].name)
                                        equipment_operation = equipment_operation.replace("{operation}", operation["name"])
                                        # equipment_operation = equipment_operation.replace("{distance}", str(operation["distance"]))
                                        equipment_operation = equipment_operation.replace("{owner}", "need" if operation["owner"] else "need not")
                                        operations[operation["name"]] = equipment_operation
                                        self.app.log("get_sight-equipment-operation: "+equipment_operation)
                                        operation_dict[operation["name"]] = (x, y)
                                        equipments[name].append(operation["name"])
                if self.app.position.get(x, dict()).get(y):
                    player_id = self.app.position.get(x, dict()).get(y)
                    if player_id == self.mud.player:
                        continue
                    if self.app.entities.get(player_id, dict()).get("Player"):
                        # player_wallet = hex(player_id)
                        name = self.app.playerid2name.get(player_id)
                        if name:
                            entities.add(name)
                            people.add(name)
                            # sub_prompt = self.config.player_prompt
                            # sub_prompt = sub_prompt.replace("{name}", name)
                            sub_prompt = ""
                            # sub_prompt = sub_prompt.replace("{passable}", "unable")
                            # sub_prompt = sub_prompt.replace("{player_id}", str(player_id))
                            # sub_prompt = sub_prompt.replace("{player_wallet}", player_wallet)
                            # load agent status & chat info
                            agent = self.app.agents[name]
                            status = agent.status
                            if status:
                                sub_prompt = sub_prompt + f"{name}'s current status is: {status}."
                            speaking = agent.language
                            if speaking:
                                sub_prompt = sub_prompt + f"{name} is speaking: {speaking}."
                            chat = self.app.entities.get(player_id, dict()).get("Chat")
                            if chat:
                                content = chat[0]
                                targetId = chat[1]
                                target_name = self.app.playerid2name.get(targetId, "")
                                info = {"source": agent.get_state("name"), "target": target_name, "content": content}
                                if info not in self.languages:
                                    self.languages.append(info)
                            chat_prompt = self.config.chat_prompt
                            chat_prompt = chat_prompt.replace("{name}", name)
                            operations[name] = chat_prompt
                            operation_dict[name] = (x, y)
                            if sub_prompt:
                                prompt += sub_prompt
                            # prompt += sub_prompt
                            # prompt += chat_prompt
                            self.app.log("get_sight-player: "+sub_prompt)
                if not prompt:
                    continue
                # x_distance = str(abs(x-cur_position[0]))
                # y_distance = str(abs(y-cur_position[1]))
                # LorR = "left" if x <= cur_position[0] else "right"
                # TorB = "down" if y <= cur_position[1] else "up"
                # prompt = prompt.replace("{x_distance}", x_distance)
                # prompt = prompt.replace("{y_distance}", y_distance)
                # prompt = prompt.replace("{LorR}", LorR)
                # prompt = prompt.replace("{TorB}", TorB)
                # self.app.log("get_sight-prompt: "+prompt)
                sight.append(prompt)
        sight = [f"You got {','.join(list(entities))} nearby."] + sight
        # if cur_position[0] > 0:
        #     direct = self.config.move_prompt.replace("{direct}", "left")
        #     operations["left"] = direct
        # if cur_position[0] < self.app.width - 1:
        #     direct = self.config.move_prompt.replace("{direct}", "right")
        #     operations["right"] = direct
        # if cur_position[1] > 0:
        #     direct = self.config.move_prompt.replace("{direct}", "up")
        #     operations["up"] = direct
        # if cur_position[0] < self.app.height - 1:
        #     direct = self.config.move_prompt.replace("{direct}", "down")
        #     operations["down"] = direct
        operations["navigate"] = self.config.navigate_prompt
        return {"observation": "".join(sight), "operations": operations, "entities": entities, "equipments": equipments, "people": people, "operation_dict": operation_dict}

    def _navigate(self, start, end):
        # 广度优先搜索
        queue = [start]
        path = {start: None}
        while queue:
            print(queue)
            # 移除队首节点并获取相邻节点
            row, col = queue.pop(0)
            if (row, col) == end:
                break
            for neighbor in self.app.neighbors(row, col):
                # 如果节点未在路径中,添加到队尾并添加到路径
                if neighbor not in path:
                    queue.append(neighbor)
                    path[neighbor] = (row, col)
        # 重构路径
        route = [end]
        while end != start:
            row, col = path.get(end, (None, None))
            if row is None:
                break
            route.append((row, col))
            end = (row, col)
        # 逆序打印路径
        route.reverse()
        return route
    
    def navigate(self, text: str, target_type: str):
        print(text, type(text))
        print(target_type, type(target_type))
        cur_position = self.app.entities.get(self.mud.player, dict()).get("Position")  # self.mud.getValue("Position", self.mud.player)
        if not cur_position:
            return
        cur_position = cur_position[0]
        # position = re.findall(r'[\d+,\d+]', text)
        # if not position:
        # location = re.findall(r'[.+]', text)
        # if not location:
        #     return
        location = text
        position = None
        print(location, self.app.locations)
        if target_type == "location" and location in self.app.locations:
            position = self.app.locations[location].get_state("enterance")
            print("to location:", position)
        if target_type == "equipment" and location in self.app.equipment2coords:
            positions = self.app.equipment2coords[location]
            nearest = -1
            for p in positions:
                if position is None:
                    position = p
                    nearest = self.distance(cur_position, p)
                elif self.distance(cur_position, p) < nearest:
                    nearest = self.distance(cur_position, p)
                    position = p
            print("to equipment:", position)
        if not position:
            print("position not found")
            return
        position = tuple(position)
        print("target position:", position)
        # position = position[0]  # eval(position[0].replace("[", "(").replace("]", ")"))
        path = self._navigate(cur_position, position)
        self.app.log("navigate path: "+str(path))
        if path:
            # remove start
            if path[0] == cur_position:
                path.pop(0)
            if path:
                next_position = path[0]
                if self.move_to(next_position[0], next_position[1]):
                    path.pop(0)
                self.move_path = path
                self.app.log("last path: "+str(self.move_path))
                # self.mud.send("Move", f"({next_position[0]},{next_position[1]})")
    
    def move(self, choice: str):
        mapping = {
            'left': [-1, 0],
            'right': [1, 0],
            'up': [0, -1],
            'down': [0, 1],
        }
        cur_position = self.app.entities.get(self.mud.player, dict()).get("Position")  # self.mud.getValue("Position", self.mud.player)
        if not cur_position:
            return
        cur_position = cur_position[0]
        x = cur_position[0] + mapping[choice][0]
        y = cur_position[1] + mapping[choice][1]
        # self.mud.send("Move", f"({x},{y})")
        return self.move_to(x, y)
    
    def move_to(self, x: int, y: int) -> bool:
        # cur_position = self.mud.getValue("Position", self.mud.player)
        # movable = self.mud.has("Movable", self.mud.player)
        # if not movable:
        #     # print("cannot move!")
        #     return False
        # encounter = self.mud.has("Encounter", self.mud.player)
        # if encounter:
        #     # print("encounter!")
        #     return False
        # new_position = (x, y)
        print("moving to:", x, y)
        # entities = self.app.position.get(x, dict()).get(y)  # self.mud.getEntitiesWithValue("Position", f"({x},{y})")
        # if entities:
        #     # print("have entity")
        #     return False
        # hash_value = self.mud.systems["Move"].send(f"executeTyped(({new_position[0]},{new_position[1]}))")['hash']
        # print(self.mud.world.w3.eth.getTransaction(hash_value))
        self.mud.send("Move", f"({x},{y})")
        return True
        # print("choice:", choice)

# if __name__ == '__main__':
#     agent = Agent()
#     while True:
#         que = input()
#         answer = agent.query('{}'.format(que))
#         print(answer)

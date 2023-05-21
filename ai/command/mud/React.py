import re
from command.command_base import CommandBase


class React(CommandBase):
    """check mud env & generate reaction."""

    def execute(self, params):
        if not self.check_params(params, ["name"]):
            return self.error('invalid params')
        name = params["name"]
        if name not in self.app.agents:
            return self.error('invalid name')
        agent = self.app.agents[name]
        time_tick = self.get_nowtime_seconds()
        reaction = agent.react("", time_tick)
        self.app.log(str(reaction))
        if "operation" in reaction:
            operation = reaction["operation"]
            if operation.get("location") and operation.get("location") != agent.get_state("location"):
                agent.navigate(operation['location'], "location")
                self.app.log("Navigating to: "+operation.get("location"))
                agent.action = "Moving to " + operation.get("location")
            elif operation.get("equipment"):
                agent.navigate(operation['equipment'], "equipment")
                # agent.action = "Moving to " + operation.get("location")
                self.app.log("Navigating to: "+operation.get("equipment")+".and will execute: "+operation["operation"])
                agent.next_operation = operation["operation"]
                agent.action = operation["operation"]
            elif operation.get("name"):
                language = operation.get("content", "")
                target_id = self.app.agents[operation.get("name")].mud.player
                self.app.log("Chatting with: "+operation.get("name")+".and content is : "+operation.get("content"))
                agent.mud.send("Chat", f'({target_id},"{language}")')
                agent.language = language
                agent.timer["chat"] = self.get_nowtime_seconds()
                agent.languages.append({"source": agent.get_state("name"), "target": operation.get("name"), "content": language})
                agent.action = "Chatting with " + operation.get("name")
            # if "choices" in operations:
            #     for choice in operations['choices']:
            #         if choice == 'navigate':
            #             # navigate
            #             agent.navigate(operations['operation'])
            #         elif choice in ['left', 'right', 'up', 'down']:
            #             # move
            #             agent.move(choice)
            #         elif choice in self.app.agents:
            #             # chat
            #             language = agent.speak(choice, reaction.get("memory_prompt", ""), reaction.get("prompt", ""), time_tick)
            #             if language:
            #                 target = ""
            #                 for name in self.app.agents.keys():
            #                     if name in language:
            #                         target = name
            #                         break
            #                 # target_id = 0
            #                 if target:
            #                     target_id = self.app.agents[target].mud.player
            #                 agent.mud.send("Chat", f'({target_id},"{language}")')
            #                 agent.language = language
            #                 agent.timer["chat"] = self.get_nowtime_seconds()
            #                 agent.languages.append({"source": agent.get_state("name"), "target": name, "content": language})
            #         else:
            #             # equipment
            #             operation_dict = reaction.get("sight", dict()).get("operation_dict", dict())
            #             position = operation_dict.get(choice)
            #             if not position:
            #                 continue
            #             entity = self.app.position.get(position[0], dict()).get(position[1])  # agent.mud.getEntitiesWithValue("Position", f"({position[0]},{position[1]})")
            #             agent.mud.send("Interaction", f'({entity},"{choice}")')
            #             agent.action = choice
        if agent.language and self.get_nowtime_seconds() > agent.timer.get("chat", 0) + 60:
            # status plan
            self.app.log("chatting time out: "+agent.language)
            agent.mud.send("CancelChat", f'{agent.mud.player}')
            agent.language = ""
            agent.timer["chat"] = 0
            agent.status = agent.action
            agent.mud.send("Status", f'"{agent.action}"')
            # agent.mud.send("Status", f'"{agent.action}"')
        # elif agent.language:
        #     # clear chat
        #     self.app.log("chatting status: ")
        #     agent.mud.send("Status", '"Chatting"')
        #     agent.status = "Chatting"
        elif agent.action:
            agent.status = agent.action
            self.app.log("status: "+agent.status)
            agent.mud.send("Status", f'"{agent.action}"')
        elif agent.move_path:
            # status move
            self.app.log("status: moving")
            agent.mud.send("Status", '"Moving"')
        # if agent.mud.getValue("Plan", f'{agent.mud.player}') != agent.plan:
        #     # new plan
        #     agent.mud.set("Plan", f'"{agent.plan}"')
        self.app.flush_events()
        return True

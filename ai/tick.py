import requests
import os
from config import Config, AgentConfig
from utils.tools import load_json_file

# cfg = Config()
abs_path = os.path.dirname(os.path.realpath(__file__))
config = Config(os.path.join(abs_path, 'config', 'app.json'))
agent_path = os.path.join(abs_path, 'config', 'agent.json')
names = list()
# Load json file.
objs = load_json_file(agent_path)
# Read data.
for obj in objs:
    cfg = AgentConfig(obj)
    # self.agent_config[config.id] = config
    names.append(cfg.id)
print(names)
agent_name = "John Lin"
for _ in range(20):
    for agent_name in names:
        data = {
            "name": agent_name
        }
        response = requests.post(f"http://{config.agent_host}:{config.agent_port}/api/mud.React", json=data)
        print(response.json())
        # break

// PlayerSystem.ts

import {
  Has,
  getComponentValue,
  EntityIndex
} from '@latticexyz/recs';

import { defineQuery } from "@latticexyz/recs";
import { SetupResult } from "../mud/setup";
import { World } from "../world/World";

import { setComponent } from "@latticexyz/recs";

export async function setup(ctx: SetupResult, world: World) {
  const {
    components: { Position, Player, Agent, Status },
    api: { joinGame },
    playerEntity,
  } = ctx;

  const playerPosition = getComponentValue(Position, playerEntity);
  const canJoinGame = getComponentValue(Player, playerEntity)?.value !== true;

  // new player
  world.MapLayer.on("click", (e: any)=>{
    if (e.type == "tile_click") {
      console.log("tile click:", e)

      if (canJoinGame) {
        joinGame(e.tile_x, e.tile_y)
      } else {
        console.log("Already joined!")
      }
    }
  })

  // current player
  if (!canJoinGame && playerPosition) {
    console.log("playerPosition:", playerPosition)

    setComponent(Status, playerEntity, {value: "Eat"})
    setComponent(Agent, playerEntity, {
      name: "Player",
      age: 13,
      occupation: "The human player",
      model: "Baby"
    })
    
    world.Viewport.moveCenter(playerPosition.x*world.TileWidth, playerPosition.y*world.TileHeight)
  }

  // others players
  const handleOtherPlayers = (entiyIndexs: EntityIndex[])=>{
    for (let playerEntity of entiyIndexs) {
      const agent = getComponentValue(Agent, playerEntity);
      const position = getComponentValue(Position, playerEntity);
      
      if (agent && position) {
        console.log("agent:", agent?.name, " online, position:", position.x, position.y)
      }
    }
  }

  let query = defineQuery([Has(Player), Has(Agent), Has(Position)], { runOnInit: true })
  handleOtherPlayers([...query.matching])
}

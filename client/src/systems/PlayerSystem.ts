// PlayerSystem.ts

import {
  Has,
  getComponentValue,
  EntityIndex
} from '@latticexyz/recs';

import { defineQuery } from "@latticexyz/recs";
import { map } from "rxjs";

import { SetupResult } from "../mud/setup";
import { World } from "../world/World";

import { setComponent } from "@latticexyz/recs";
import { State as StateType } from "../mud/components/State";

export async function setup(ctx: SetupResult, world: World) {
  const {
    components: { Position, Player, Agent, State, Status },
    api: { joinGame },
    playerEntity,
  } = ctx;

  const playerPosition = getComponentValue(Position, playerEntity);
  const canJoinGame = getComponentValue(Player, playerEntity)?.value !== true;

  // new player
  world.Map.on("click", (e: any)=>{
    if (e.type == "tile_click") {
      console.log("tile click:", e)

      if (canJoinGame) {
        joinGame(e.tile_x, e.tile_y)
        setComponent(State, playerEntity, {value: StateType.Idle})
      }
    }
  })

  // current player
  if (!canJoinGame && playerPosition) {
    console.log("playerPosition:", playerPosition)

    setComponent(State, playerEntity, {value: StateType.Idle})
    setComponent(Status, playerEntity, {value: "Eat"})
    setComponent(Agent, playerEntity, {
      name: "Player",
      age: 13,
      occupation: "The human player",
      model: "Baby"
    })
  }

  // others players
  const handleOtherPlayers = (entiyIndexs: EntityIndex[])=>{
    for (let playerEntity of entiyIndexs) {
      setComponent(State, playerEntity, {value: StateType.Idle})
    }
  }

  let query = defineQuery([Has(Player), Has(Position)], { runOnInit: true })
  query.update$
      .pipe(map(() => [...query.matching]))
      .subscribe((entities) => handleOtherPlayers(entities))

  handleOtherPlayers([...query.matching])
}

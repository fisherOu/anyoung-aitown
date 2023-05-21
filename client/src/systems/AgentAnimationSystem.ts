// RotationSystem.ts

import * as PIXI from 'pixi.js';
import {
  defineSystem,
  Has,
  getComponentValue,
} from '@latticexyz/recs';

import { SetupResult } from "../mud/setup";
import { World } from "../world/World";

import { clientComponents, contractComponents } from "../mud/components"
import { State as StateType } from "../mud/components/State";

const Agent = contractComponents.Agent;
const Position = contractComponents.Position;
const State = clientComponents.State;

const CompomentName = "animation";

export async function setup(ctx: SetupResult, world: World) {
  const spritesheet = await PIXI.Assets.load(`${ctx.publicURL}/assets/characters/characters&GUI.json`) as PIXI.Spritesheet;
  console.log("FightResultSystem init spritesheet:", spritesheet)

  await spritesheet.parse();

  const createAnimation = (actor: string, state: number)=>{
    let textures = new Array<PIXI.Texture>();

    switch (state) {
      case StateType.Idle:
        textures.push(spritesheet.textures[`${actor}_walk_forwards/${actor}_walk_forwards_02.png`])
        break;
      case StateType.WalkBackwards:
        textures = spritesheet.animations[`${actor}_walk_backwards/${actor}_walk_backwards`]
        break;
      case StateType.WalkEastwards:
        textures = spritesheet.animations[`${actor}_walk_eastwards/${actor}_walk_eastwards`]
        break;
      case StateType.WalkForwards:
        textures = spritesheet.animations[`${actor}_walk_forwards/${actor}_walk_forwards`]
        break;
      case StateType.WalkWestwards:
        textures = spritesheet.animations[`${actor}_walk_Westwards/${actor}_walk_Westwards`]
        break;
    }

    let animation = new PIXI.AnimatedSprite(
      textures,
    );

    animation.anchor.set(0.5);
    animation.animationSpeed = 0.05;
    animation.play();

    return animation
  }

  defineSystem(ctx.world, [Has(Position), Has(State)], (update) => {
    const entity = world.getOrCreateEntity(update.entity)
    const agent = getComponentValue(Agent, update.entity);
    const position = getComponentValue(Position, update.entity);
    const state = getComponentValue(State, update.entity);
  
    if (agent && state && position) {
      let animation = createAnimation(agent.model, state.value)
      animation.name = CompomentName
      
      entity.x = position.x * 16 + 8;
      entity.y = position.y * 16 + 8;

      let old = entity.getChildByName(CompomentName)
      if (old) {
        old.removeFromParent()
      }

      entity.addChild(animation);
    }
  });
}


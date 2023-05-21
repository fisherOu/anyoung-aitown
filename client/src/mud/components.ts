import { overridableComponent, defineComponent, Type } from "@latticexyz/recs";
import {
  defineBoolComponent,
  defineCoordComponent,
  defineNumberComponent,
  defineStringComponent,
} from "@latticexyz/std-client";

import {
  defineAnimationComponent,
} from "./components/Animation";

import {
  defineStateComponent,
} from "./components/State";

import { world } from "./world";

export const contractComponents = {
  Counter: defineNumberComponent(world, {
    metadata: {
      contractId: "component.Counter",
    },
  }),
  Encounter: defineStringComponent(world, {
    metadata: {
      contractId: "component.Encounter",
    },
  }),
  Encounterable: defineBoolComponent(world, {
    metadata: {
      contractId: "component.Encounterable",
    },
  }),
  EncounterTrigger: defineBoolComponent(world, {
    metadata: {
      contractId: "component.EncounterTrigger",
    },
  }),
  MapConfig: defineComponent(
    world,
    {
      width: Type.Number,
      height: Type.Number,
      terrain: Type.String,
    },
    {
      id: "MapConfig",
      metadata: { contractId: "component.MapConfig" },
    }
  ),
  MonsterType: defineNumberComponent(world, {
    metadata: {
      contractId: "component.MonsterType",
    },
  }),
  Movable: defineBoolComponent(world, {
    metadata: {
      contractId: "component.Movable",
    },
  }),
  Obstruction: defineBoolComponent(world, {
    metadata: {
      contractId: "component.Obstruction",
    },
  }),
  OwnedBy: defineStringComponent(world, {
    metadata: {
      contractId: "component.OwnedBy",
    },
  }),
  Player: overridableComponent(
    defineBoolComponent(world, {
      metadata: {
        contractId: "component.Player",
      },
    })
  ),
  Position: overridableComponent(
    defineCoordComponent(world, {
      metadata: {
        contractId: "component.Position",
      },
    })
  ),
  Name: defineStringComponent(world, {
    metadata: {
      contractId: "component.Name",
    },
  }),
  Agent: defineComponent(
    world,
    {
      name: Type.String,
      age: Type.Number,
      occupation: Type.String,
      model: Type.String,
    },
    {
      id: "Agent",
      metadata: { contractId: "component.Agent" },
    }
  ),
  Status: defineStringComponent(world, {
    metadata: {
      contractId: "component.Status",
    },
  }),
  Chat: defineComponent(
    world,
    {
      chat_detail: Type.String,
      target_id: Type.Number,
    },
    {
      id: "Chat",
      metadata: { contractId: "component.Chat" },
    }
  ),
};

export const clientComponents = {
  Rotation: defineComponent(world, { 
    value: Type.Number 
  }),
  Animation: defineAnimationComponent(world),
  State: defineStateComponent(world)
};
import * as PIXI from 'pixi.js';
import { EntityID, EntityIndex } from '@latticexyz/recs';
import { MudWorld } from '../mud/world';

export class World extends PIXI.utils.EventEmitter{
  private mudWorld: MudWorld;
  private entities: Map<EntityID, PIXI.Container>
  private map: PIXI.Container;

  public constructor(mudWorld: MudWorld, map: PIXI.Container){
    super()

    this.mudWorld = mudWorld;
    this.map = map;
    this.entities = new Map<EntityID, PIXI.Container>();
  }

  public get Map () {
    return this.map
  }

  public getOrCreateEntity(index: EntityIndex): PIXI.Container {
    let entityId = this.mudWorld.entities[index]
    let entity = this.entities.get(entityId)

    if (!entity) {
      entity = new PIXI.Container()
      entity.x = 0;
      entity.y = 0;
      
      this.map.addChild(entity)
      this.entities.set(entityId, entity)
    }

    return entity;
  }
}
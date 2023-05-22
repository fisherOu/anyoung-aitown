import * as PIXI from 'pixi.js';
import { EntityID, EntityIndex } from '@latticexyz/recs';
import { Viewport } from 'pixi-viewport';
import { MudWorld } from '../mud/world';
import { Observable } from "rxjs";

export class World extends PIXI.utils.EventEmitter{
  private mudWorld: MudWorld;
  private entities: Map<EntityID, PIXI.Container>
  private viewport: Viewport;
  private mapLayer: PIXI.Container;
  private entityLayer: PIXI.Container;
  private ticker: PIXI.Ticker
  private tileWidth: number;
  private tileHeight: number;

  public constructor(mudWorld: MudWorld, viewport: Viewport, map: PIXI.Container, ticker: PIXI.Ticker, tileWidth: number, tileHeight: number){
    super()

    this.mudWorld = mudWorld;
    this.ticker = ticker;
    this.tileWidth = tileWidth;
    this.tileHeight = tileHeight;
    this.entityLayer = new PIXI.Container();
    this.entities = new Map<EntityID, PIXI.Container>();

    this.viewport = viewport;
    this.mapLayer = map;

    this.entityLayer.x = tileWidth * 12;
    this.entityLayer.y = 0;
    this.viewport.addChild(this.entityLayer)
  }

  public get Viewport () {
    return this.viewport
  }

  public get MapLayer () {
    return this.mapLayer
  }

  public get EntityLayer () {
    return this.entityLayer
  }

  public get TileWidth () {
    return this.tileWidth
  }

  public get TileHeight () {
    return this.tileHeight
  }

  public get $update ():Observable<number> {
    const source = new Observable<number>((subscriber) => {
      this.ticker.add((ts:number)=>{
        subscriber.next(ts);
      })
    });

    return source
  }

  public getOrCreateEntity(index: EntityIndex): PIXI.Container {
    let entityId = this.mudWorld.entities[index]
    let entity = this.entities.get(entityId)

    if (!entity) {
      entity = new PIXI.Container()
      entity.x = 0;
      entity.y = 0;
      
      this.entityLayer.addChild(entity)
      this.entities.set(entityId, entity)
    }

    return entity;
  }
}
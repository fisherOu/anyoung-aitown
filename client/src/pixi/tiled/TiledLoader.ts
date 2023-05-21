import * as PIXI from "pixi.js";

export class TiledLoader extends PIXI.utils.EventEmitter{
  private async getTilesetTexture(tilesetId: number, tilesets: any[], basePath: string): Promise<PIXI.Texture> {
    const tileset = tilesets.find((tileset) => tileset.firstgid <= tilesetId && tilesetId < (tileset.firstgid + tileset.tilecount));
  
    if (!tileset) {
      throw new Error(`Tileset for tile id ${tilesetId} not found.`);
    }
  
    const textureUrl = basePath + tileset.image;
    const texture = await PIXI.Assets.load(textureUrl);
    if (texture && texture.baseTexture) {
      texture.baseTexture.scaleMode = PIXI.SCALE_MODES.NEAREST;
    }
    
    const textures: PIXI.Texture[] = [];
  
    const tilesPerRow = Math.floor((tileset.imagewidth - tileset.margin) / (tileset.tilewidth + tileset.spacing));
    const numRows = Math.ceil(tileset.tilecount / tilesPerRow);
  
    for (let row = 0; row < numRows; row++) {
      for (let col = 0; col < tilesPerRow; col++) {
        const x = tileset.margin + col * (tileset.tilewidth + tileset.spacing);
        const y = tileset.margin + row * (tileset.tileheight + tileset.spacing);
        const rect = new PIXI.Rectangle(x, y, tileset.tilewidth, tileset.tileheight);
        textures.push(new PIXI.Texture(texture.baseTexture, rect));
      }
    }
  
    return textures[tilesetId - tileset.firstgid];
  }
  
  private async processLayers(parent: PIXI.Container, mapData: any, layers: any[], tilesets: any[], basePath: string): Promise<PIXI.Container[]> {
    const containers: PIXI.Container[] = [];

    for (const layer of layers) {
      if (layer.type === "tilelayer") {
        const tileLayerContainer = new PIXI.Container();
        const data = layer.data as number[];

        for (let y = 0; y < layer.height; y++) {
          for (let x = 0; x < layer.width; x++) {
            const tileId = data[y * layer.width + x];

            if (tileId !== 0) {
              const tileTexture = await this.getTilesetTexture(tileId, tilesets, basePath);
              const sprite = new PIXI.Sprite(tileTexture);

              sprite.x = x * mapData.tilewidth;
              sprite.y = y * mapData.tileheight;

              sprite.interactive = true

              sprite.on('pointerdown', (e: any)=>{
                this.handleTileClick(parent, mapData, e)
              });

              tileLayerContainer.addChild(sprite);
            }
          }
        }

        containers.push(tileLayerContainer);
      } else if (layer.type === "group") {
        const groupContainers = await this.processLayers(parent, mapData, layer.layers, tilesets, basePath);
        containers.push(...groupContainers);
      }
    }

    return containers;
  }

  private handleTileClick(_parent:PIXI.Container, mapData:any, e:any) {
    console.log("source event:", e)

    this.emit("tile_click", {
      type: "tile_click",
      tile_x: Math.round(e.target.x/mapData.tilewidth),
      tile_y: Math.round(e.target.y/mapData.tileheight)
    })
  }

  public async load(url: string): Promise<PIXI.Container> {
    const mapData = await PIXI.Assets.load(url);
    const basePath = new URL(url).origin + new URL(url).pathname.split('/').slice(0, -1).join('/') + '/';
    const container = new PIXI.Container();

    // Add map dimensions to the container
    container.width = mapData.width * mapData.tilewidth;
    container.height = mapData.height * mapData.tileheight;

    const layers = await this.processLayers(container, mapData, mapData.layers, mapData.tilesets, basePath);

    for (const layer of layers) {
      container.addChild(layer);
    }

    return container;
  }
}

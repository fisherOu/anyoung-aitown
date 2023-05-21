// MainScene.tsx
import * as PIXI from 'pixi.js';
import { useRef, useEffect } from 'react';
import { Viewport } from 'pixi-viewport';
import {TiledLoader} from '../pixi/tiled/TiledLoader'

import { SetupResult } from "../mud/setup"
import { useMUD } from "../MUDContext";

import { World } from "../world/World";

import { setup as setupMoveSystem } from "../systems/MoveSystem"
import { setup as setupAgentAnimationSystem } from "../systems/AgentAnimationSystem";
import { setup as setupPlayerSystem } from "../systems/PlayerSystem";
import { setup as setupStatusSystem } from "../systems/StatusSystem";

const laodMap = async (ctx: SetupResult, app: PIXI.Application): Promise<PIXI.Container> => {
    let loader = new TiledLoader();

    // Adjust the path to your actual map file and its assets
    let layer = await loader.load(`${ctx.publicURL}/assets/map/Game-map_0.json`)

    console.log("layer width:", layer.width, "height:", layer.height);

    const viewport = new Viewport({
      screenWidth: window.innerWidth,
      screenHeight: window.innerHeight,
      worldWidth: layer.width, // Set to your map dimensions
      worldHeight: layer.height,
      events: app.renderer.events,
    });

    // activate plugins
    viewport
      .drag()
      .pinch()  
      .wheel()
      .decelerate()

    // center map
    viewport.zoomPercent(2)
    viewport.moveCenter(layer.width/2, layer.height/2)

    viewport.addChild(layer);
    app.stage.addChild(viewport);

    loader.on("tile_click", (e: any)=>{
      layer.emit("click", e)
    })

    return layer
}

const setupGame = async (ctx: SetupResult, app: PIXI.Application)=> {
  let map = await laodMap(ctx, app)
  let world = new World(ctx.world, map)

  // setup sytems
  await setupMoveSystem(ctx, world)
  await setupPlayerSystem(ctx, world)
  await setupAgentAnimationSystem(ctx, world)
  await setupStatusSystem(ctx, world)

  app.start();
}

const MainScene = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const ctx = useMUD();

  useEffect(() => {
    const app = new PIXI.Application({
      view: canvasRef.current!,
      width: window.innerWidth,
      height: window.innerHeight,
      backgroundColor: 0xffffff,
      autoStart: false, // 关闭自动渲染
      antialias: false,
      autoDensity: true // 确保渲染器大小与画布大小相同
    });

    setupGame(ctx, app)
    
    return () => {
      app.destroy(true);
    };
  }, []);

  return (
    <div>
      <canvas ref={canvasRef} />
    </div>
  );
};

export default MainScene;

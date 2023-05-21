// SPDX-License-Identifier: MIT
pragma solidity >=0.8.0;
import { IWorld } from "solecs/interfaces/IWorld.sol";
import { MapConfigComponent, ID as MapConfigComponentID, MapConfig } from "components/MapConfigComponent.sol";
import { PositionComponent, ID as PositionComponentID, Coord } from "components/PositionComponent.sol";
import { ObstructionComponent, ID as ObstructionComponentID } from "components/ObstructionComponent.sol";
import { EncounterTriggerComponent, ID as EncounterTriggerComponentID } from "components/EncounterTriggerComponent.sol";

import { ItemMetadataComponent, ID as ItemMetadataComponentID, ItemMetadata } from "components/ItemMetadataComponent.sol";
import { Boundary2DComponent, ID as Boundary2DComponentID, Boundary2D } from "components/Boundary2DComponent.sol";
import { InteractiveComponent, ID as InteractiveComponentID } from "components/InteractiveComponent.sol";
import { EquipmentTypeComponent, ID as EquipmentTypeComponentID, EquipmentType } from "components/EquipmentTypeComponent.sol";

import { TerrainType } from "../TerrainType.sol";
import { LibAreas } from "./LibAreas.sol";
import { LibInteractiveObjects } from "./LibInteractiveObjects.sol";
import { LibEquipmentProperties } from "./LibEquipmentProperties.sol";

library MapConfigInitializer {

  // Init Map
  function initMap(IWorld world) internal {
    MapConfigComponent mapConfig = MapConfigComponent(world.getComponent(MapConfigComponentID));
    PositionComponent position = PositionComponent(world.getComponent(PositionComponentID));
    ObstructionComponent obstruction = ObstructionComponent(world.getComponent(ObstructionComponentID));

    uint8[30][30] memory map = [
      [2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2],
      [2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,0,0,0,0,0,0,0,2],
      [2,2,2,2,2,2,2,2,2,2,2,0,0,0,2,2,2,2,2,2,0,0,0,0,0,0,0,0,0,2],
      [2,2,2,2,2,2,2,0,0,0,0,0,0,0,0,0,0,0,2,2,0,2,2,2,2,2,2,2,2,2],
      [2,2,2,2,2,2,2,2,2,2,0,0,0,0,0,2,2,2,2,2,0,2,2,2,2,2,2,2,2,2],
      [2,2,2,2,2,2,2,2,2,2,2,0,0,0,0,2,2,2,2,2,0,2,2,0,2,2,2,2,2,2],
      [2,2,2,2,2,2,2,2,2,2,2,0,0,0,2,2,2,2,2,2,0,2,2,2,0,0,0,2,2,2],
      [2,2,2,2,2,2,2,2,2,2,2,0,0,0,0,2,2,2,2,2,0,2,2,0,0,2,0,2,2,2],
      [2,2,2,2,2,2,2,2,2,2,0,0,0,0,0,0,2,0,2,2,0,2,0,0,2,2,2,0,0,2],
      [2,2,2,2,2,2,2,0,0,0,0,0,0,0,0,2,2,2,2,2,0,2,2,0,0,2,0,0,2,2],
      [2,2,2,2,2,2,2,2,2,2,0,2,2,0,2,2,2,2,2,2,0,2,2,2,0,0,0,2,2,2],
      [2,2,2,2,2,2,2,2,2,2,0,2,2,0,0,0,0,0,2,2,0,2,2,0,0,0,0,0,2,2],
      [2,2,2,2,2,2,0,0,0,0,0,0,2,0,0,0,2,2,2,2,0,2,2,2,0,0,0,0,2,2],
      [2,2,2,2,2,2,0,0,0,0,0,0,2,2,2,2,2,2,2,2,0,0,0,0,0,0,0,0,0,0],
      [2,2,2,2,2,2,0,0,0,0,0,0,2,2,2,2,2,2,2,2,0,0,0,0,0,0,0,0,0,0],
      [2,2,2,2,2,2,0,0,0,0,0,0,0,0,0,0,0,0,0,2,0,0,2,2,0,0,0,0,0,0],
      [2,2,2,2,2,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,2,0,0,0,0,0,0],
      [2,2,2,2,2,2,2,2,0,0,0,0,0,0,0,0,0,0,0,0,2,0,0,0,0,0,0,0,0,0],
      [2,2,2,2,2,2,2,2,0,0,0,2,2,2,2,2,2,2,2,0,2,0,2,2,0,0,0,0,0,0],
      [2,2,2,2,2,2,2,2,0,0,0,0,0,0,0,2,2,2,2,0,0,0,0,2,0,0,0,0,0,0],
      [2,2,2,2,2,2,2,2,0,0,0,2,2,2,2,2,2,2,2,0,2,0,0,2,0,0,0,0,0,0],
      [2,2,2,2,2,2,2,2,0,0,0,2,2,2,2,2,2,0,2,0,2,0,0,2,0,0,0,0,0,0],
      [2,2,2,2,2,2,2,2,2,0,2,2,2,2,2,2,2,0,2,0,0,0,0,2,0,0,0,0,0,0],
      [2,2,2,2,2,2,2,2,2,0,2,2,2,2,2,2,2,0,0,0,0,0,0,2,0,0,0,0,0,0],
      [2,2,2,2,2,2,2,2,0,0,0,2,2,2,2,2,2,0,2,0,0,0,0,2,0,0,0,0,0,0],
      [2,2,2,2,2,2,2,0,0,0,0,2,2,2,2,2,2,0,2,0,0,0,0,2,0,0,0,0,0,0],
      [2,2,2,2,2,2,2,2,0,0,0,0,0,0,0,0,0,0,2,0,0,0,0,2,0,0,0,0,0,0],
      [2,2,2,2,2,2,2,2,0,0,2,2,0,0,0,2,2,2,2,0,0,0,0,2,2,2,0,2,2,2],
      [2,2,2,2,2,2,2,2,0,0,2,2,2,2,2,2,2,2,2,0,0,0,0,2,2,2,0,2,2,2],
      [2,2,2,2,2,2,2,2,0,0,2,2,2,2,2,2,2,2,0,0,0,0,0,0,0,0,0,0,0,0]
    ];

    uint32 height = uint32(map.length);
    uint32 width = uint32(map[0].length);
    bytes memory terrain = new bytes(width * height);

    for (uint32 y = 0; y < height; y++) {
      for (uint32 x = 0; x < width; x++) {
        uint8 terrainType = map[y][x];
        if (terrainType == uint8(TerrainType.None)) continue;

        terrain[(y * width) + x] = bytes1(terrainType);

        if (terrainType == uint8(TerrainType.Boulder)) {
          uint256 entity = world.getUniqueEntityId();
          position.set(entity, Coord(int32(x), int32(y)));
          obstruction.set(entity);
        }
      }
    }

    mapConfig.set(MapConfig({ width: width, height: height, terrain: terrain }));
  }

  // Init Area
  function initArea(IWorld world) internal {
    ItemMetadataComponent itemMetadata = ItemMetadataComponent(world.getComponent(ItemMetadataComponentID));
    Boundary2DComponent boundary = Boundary2DComponent(world.getComponent(Boundary2DComponentID));

    LibAreas.AreaInfo[] memory areaInfos = LibAreas.getAreas();
    uint256 areaSize = areaInfos.length;

    for (uint256 i = 0; i < areaSize; i++) {
      uint256 entity = world.getUniqueEntityId();

      LibAreas.AreaInfo memory areaInfo = areaInfos[i];
      itemMetadata.set(entity, ItemMetadata("", areaInfo.name, ""));
      boundary.set(entity, Boundary2D(int32(areaInfo.x), int32(areaInfo.y), int32(areaInfo.x + areaInfo.width), int32(areaInfo.y + areaInfo.height)));
    }
  }

  // Init InteractiveObjects
  function initObjects(IWorld world) internal {
   ItemMetadataComponent itemMetadata = ItemMetadataComponent(world.getComponent(ItemMetadataComponentID));
    Boundary2DComponent boundary = Boundary2DComponent(world.getComponent(Boundary2DComponentID));
    InteractiveComponent interactive = InteractiveComponent(world.getComponent(InteractiveComponentID));

    LibInteractiveObjects.InteractiveObject[] memory interactiveObjects = LibInteractiveObjects.getAllInteractiveObjects();
    uint256 objectSize = interactiveObjects.length;

    for (uint256 i = 0; i < objectSize; i++) {
      uint256 entity = world.getUniqueEntityId();

      LibInteractiveObjects.InteractiveObject memory obj = interactiveObjects[i];
      itemMetadata.set(entity, ItemMetadata("", obj.name, ""));
      boundary.set(entity, Boundary2D(int32(obj.x), int32(obj.y), int32(obj.x + obj.width), int32(obj.y + obj.height)));
      interactive.set(entity);
    }
  }


  // Init
  function init(IWorld world) internal {
    initMap(world);
    initArea(world);
    initObjects(world);
  }
}

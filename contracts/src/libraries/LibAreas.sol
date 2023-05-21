// SPDX-License-Identifier: MIT
pragma solidity >=0.8.0;

library LibAreas {
    struct AreaInfo {
        string name;
        int32 x;
        int32 y;
        int32 width;
        int32 height;
    }

    function getAreas() internal pure returns (AreaInfo[] memory) {
        AreaInfo[] memory areas = new AreaInfo[](3);
        areas[0] = AreaInfo("Park", 4, 18, 15, 12);
        areas[1] = AreaInfo("House", 6, 1, 13, 14);
        areas[2] = AreaInfo("Cafe", 21, 4, 9, 9);
        return areas;
    }
}
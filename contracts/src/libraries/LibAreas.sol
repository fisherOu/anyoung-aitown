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
        AreaInfo[] memory areas = new AreaInfo[](14);
        areas[0] = AreaInfo("Broadcast plaza", 109, 15, 26, 19);
        areas[1] = AreaInfo("Lin's house", 26, 54, 31, 16);
        areas[2] = AreaInfo("Playground", 62, 65, 16, 26);
        areas[3] = AreaInfo("Park", 15, 8, 39, 31);
        areas[4] = AreaInfo("Casino", 71, 16, 24, 17);
        areas[5] = AreaInfo("Disco", 83, 33, 13, 18);
        areas[6] = AreaInfo("Cafe", 70, 33, 13, 18);
        areas[7] = AreaInfo("Art plaza", 123, 42, 12, 10);
        areas[8] = AreaInfo("Communication plaza", 109, 42, 12, 10);
        areas[9] = AreaInfo("Yamamoto's house", 79, 65, 12, 26);
        areas[10] = AreaInfo("House D", 93, 65, 28, 13);
        areas[11] = AreaInfo("House E", 93, 78, 28, 13);
        areas[12] = AreaInfo("Taylor's house", 123, 65, 12, 26);
        areas[13] = AreaInfo("Moore's house", 26, 71, 31, 19);
        return areas;
    }
}
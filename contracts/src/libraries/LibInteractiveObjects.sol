// SPDX-License-Identifier: MIT
pragma solidity >=0.8.0;

library LibInteractiveObjects {
    struct InteractiveObject {
        string name;
        int32 x;
        int32 y;
        int32 width;
        int32 height;
    }

    function getAllInteractiveObjects() internal pure returns (InteractiveObject[] memory) {
        InteractiveObject[] memory allInteractiveObjects = new InteractiveObject[](24);
        allInteractiveObjects[0] = InteractiveObject('Bed', 8, 3, 2, 1);
        allInteractiveObjects[1] = InteractiveObject('Cabinet', 18, 3, 1, 1);
        allInteractiveObjects[2] = InteractiveObject('Bookshelf', 9, 6, 2, 2);
        allInteractiveObjects[3] = InteractiveObject('Bookshelf', 18, 6, 2, 2);
        allInteractiveObjects[4] = InteractiveObject('Bed', 15, 3, 2, 1);
        allInteractiveObjects[5] = InteractiveObject('Table', 10, 6, 1, 2);
        allInteractiveObjects[6] = InteractiveObject('Cabinet', 8, 3, 1, 1);
        allInteractiveObjects[7] = InteractiveObject('Cabinet', 15, 3, 1, 1);
        allInteractiveObjects[8] = InteractiveObject('Table', 16, 6, 1, 2);
        allInteractiveObjects[9] = InteractiveObject('Cabinet', 11, 3, 1, 1);
        allInteractiveObjects[10] = InteractiveObject('Table', 18, 10, 3, 2);
        allInteractiveObjects[11] = InteractiveObject('Fence', 18, 24, 9, 6);
        allInteractiveObjects[12] = InteractiveObject('Fence', 18, 18, 8, 5);
        allInteractiveObjects[13] = InteractiveObject('Fence', 12, 17, 1, 17);
        allInteractiveObjects[14] = InteractiveObject('Fence', 27, 1, 11, 3);
        allInteractiveObjects[15] = InteractiveObject('Fence', 29, 24, 3, 2);
        allInteractiveObjects[16] = InteractiveObject('Fence', 25, 24, 4, 11);
        allInteractiveObjects[17] = InteractiveObject('Fence', 20, 14, 1, 2);
        allInteractiveObjects[18] = InteractiveObject('Fence', 20, 11, 1, 14);
        allInteractiveObjects[19] = InteractiveObject('Lamp', 20.0, 17, 1.0, 2);
        allInteractiveObjects[20] = InteractiveObject('Lamp', 23.0, 12, 1.0, 2);
        allInteractiveObjects[21] = InteractiveObject('Lake', 15, 11, 7, 6);
        allInteractiveObjects[22] = InteractiveObject('Lake', 7, 11, 21, 30);
        allInteractiveObjects[23] = InteractiveObject('Cabinet', 8.0, 8.0, 1, 1);
        return allInteractiveObjects;
    }
}
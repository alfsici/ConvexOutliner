# -*- coding: utf-8 -*-

import time

try:
    from maya import cmds
    from maya import OpenMaya
    from maya import OpenMayaUI
except:
    pass

from scipy import array
from scipy.spatial import ConvexHull


class ConvexOutliner(object):
    """
    :class:`ConvexOutliner` Oriented Bounding Box Class.

    Requires an input meshName.
    """
    def __init__(self, meshName=None, projectOnPlane=True):

        if not meshName:
            raise RuntimeError("No mesh set in class.")

        self.shapeName = self.getShape(meshName)
        self.fnMesh = self.getMFnMesh(self.shapeName)
        self.activeView = OpenMayaUI.M3dView.active3dView()
        self.dagCamera = OpenMaya.MDagPath()
        self.activeView.getCamera(self.dagCamera)
        self.fnCamera = OpenMaya.MFnCamera(self.dagCamera)
        self.eyePoint = OpenMaya.MVector(
            self.fnCamera.eyePoint(OpenMaya.MSpace.kWorld))

        self.vtxPoints = self.getPoints(self.fnMesh)
        self.screenPoints = self.get2dPoints(self.vtxPoints)
        self.hull = ConvexHull(self.screenPoints)
        self.indexes = self.hull.vertices
        self.outlinePoints = [[self.vtxPoints[i].x,
                               self.vtxPoints[i].y,
                               self.vtxPoints[i].z]
                              for i in self.indexes]

        if projectOnPlane:
            self.projectPoints()

    def buildCurve(self, closeCurve=True):
        """
        Get the points of each vertex in screen space.

        Raises:
            None

        Returns:
            (string) curve name.
        """
        if closeCurve:
            self.outlinePoints.append(self.outlinePoints[0])
            curve = cmds.curve(
                periodic=True,
                point=self.outlinePoints,
                degree=1,
                knot=range(len(self.outlinePoints)))
        else:
            curve = cmds.curve(
                point=self.outlinePoints,
                degree=1)

        return curve

    def projectPoints(self):
        """
        Project points to mean distance.

        Raises:
            None

        Returns:
            (string) curve name.
        """
        vecPnts = [OpenMaya.MVector(*pnt) for pnt in self.outlinePoints]
        distances = [(vecPnt - self.eyePoint).length()
                     for vecPnt in vecPnts]
        mean = sum(distances)/len(distances)

        for i, vecPnt in enumerate(vecPnts):
            reprojectPnt = (vecPnt - self.eyePoint)
            reprojectPnt.normalize()

            reprojectPnt *= mean
            reprojectPnt += self.eyePoint

            self.outlinePoints[i] = [reprojectPnt.x,
                                     reprojectPnt.y,
                                     reprojectPnt.z]

    def get2dPoints(self, vtxPoints):
        """
        Get the points of each vertex in screen space.

        :param vtxPoints (OpenMaya.MVectorArray): mesh function set.

        Raises:
            None

        Returns:
            (list of list) 2d points.
        """
        # Pointer hoop-jumping.
        xPtrInit = OpenMaya.MScriptUtil()
        yPtrInit = OpenMaya.MScriptUtil()
        xPtr = xPtrInit.asShortPtr()
        yPtr = yPtrInit.asShortPtr()

        screenPoints = []
        for p in xrange(vtxPoints.length()):
            self.activeView.worldToView(vtxPoints[p], xPtr, yPtr)

            screenPoints.append([xPtrInit.getShort(xPtr),
                                 yPtrInit.getShort(yPtr)])

        return array(screenPoints)

    def getPoints(self, fnMesh):
        """
        Get the points of each vertex.

        :param fnMesh (OpenMaya.MFnMesh): mesh function set.

        Raises:
            None

        Returns:
            (OpenMaya.MVectorArray) list of points.
        """
        mPoints = OpenMaya.MPointArray()
        fnMesh.getPoints(mPoints, OpenMaya.MSpace.kWorld)

        return mPoints

    def getMFnMesh(self, mesh):
        """
        Gets the MFnMesh of the input mesh.

        :param mesh (str): string name of input mesh.

        Raises:
            `RuntimeError` if not a mesh.
        Returns:
            (OpenMaya.MFnMesh) MFnMesh mesh object.
        """
        mSel = OpenMaya.MSelectionList()
        mSel.add(mesh)

        mDagMesh = OpenMaya.MDagPath()
        mSel.getDagPath(0, mDagMesh)

        try:
            fnMesh = OpenMaya.MFnMesh(mDagMesh)
        except:
            raise RuntimeError("%s is not a mesh.")

        return fnMesh

    def getShape(self,  node):
        """
        Gets the shape node from the input node.

        :param node (str): string name of input node

        Raises:
            `RuntimeError` if no shape node.
        Returns:
            (str) shape node name
        """
        if cmds.nodeType(node) == 'transform':
            shapes = cmds.listRelatives(node, shapes=True)

            if not shapes:
                raise RuntimeError('%s has no shape' % node)

            return shapes[0]

        elif cmds.nodeType(node) == "mesh":
            return node

if __name__ == '__main__':

    mesh = cmds.ls(selection=True)

    if len(mesh) == 0:
        raise RuntimeError("Nothing selected!")

    cv = ConvexOutliner(mesh[0])
    print cv.buildCurve()

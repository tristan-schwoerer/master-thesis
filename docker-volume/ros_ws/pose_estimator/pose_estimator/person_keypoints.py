
import numpy as np


def calculate3DPoint(depth, xImage, yImage, depthRadiusX: int = 1, depthRadiusY: int = 1, resolutionX = 640, resolutionY = 480, HFOV = 54.732, VFOV = 42.4115):

    """
    Parameters
    ----------
    depth : numpy array 
        numpy array of depth aligned with the image for detections
    Return
    ----------
    distance : float
        distance to the detected person in meters
    angle : float
        angle to the centre of the bounding box of the person
    """

    #relative to the image center such that the distances are postive going left and upwards according to REP
    centreX = (resolutionX/2) - xImage
    centreY = (resolutionY/2) - yImage

    #Length of the distance to the virtual image plane
    Id = (resolutionX/2)/np.tan(HFOV/2)
    #Length of the hypothenuse going towards the bb on the y=centrey plane
    Idx = np.sqrt((Id**2) + (centreX**2))

    #angle between Idx and the line going from the camera to the centre of the bb
    delta = np.arctan2(centreY,Idx)

    #Angle between idx and ID
    gamma = np.arctan2(centreX,Id)

    ##get distances of depth image assuming same resolution and allignment relative to bounding box coordinates
    distBox = depth[ int(max(yImage-depthRadiusY,0)):
                    int(min(yImage+depthRadiusY,resolutionY)),
                    int(max(xImage-depthRadiusX,0)):
                    int(min(xImage+depthRadiusX,resolutionX))]
    distBox = distBox.flatten()

    distBox = np.delete(distBox, np.argwhere(distBox == 0))

    distance = np.nanmedian(distBox)

    #Projection to horizontal plane happening here
    distance = distance*np.cos(delta)
    #Output in polar coordinates such that angles to the left are positive and angles to the right are negative
    #Distance Forward is positiv backwards not possible
    #return x andy according to REP
    xRobot = np.sin(gamma) * distance
    yRobot = np.cos(gamma) * distance
    return xRobot,yRobot

class keypoint():
    ID: str
    xImage:float
    yImage:float
    x =float
    y=float
    z=float

    def __init__(self, ID: int, xImage: float, yImage: float, depthRadius: int = 2 ):
        self.ID=ID
        self.xImage=xImage
        self.yImage=yImage
        self.x=None
        self.y=None
        self.depthRadius=depthRadius
    
    def calculate3DKeyoint(self, depth):
        self.x,self.y=calculate3DPoint(depth = depth, xImage = self.xImage, yImage = self.yImage, depthRadiusX = self.depthRadius, depthRadiusY = self.depthRadius)
        
    
class person_keypoint:
    '''
    Keypoints for one detection are passed to this object for calculation of 3D location and orientation
    '''
    def __init__(self, keypoints,depth):
        # self.IDnames = np.array(["nose", "left_eye", "right_eye", "left_ear",
        #                    "right_ear", "left_shoulder", "right_shoulder",
        #                    "left_elbow", "right_elbow", "left_wrist",
        #                    "right_wrist", "left_hip", "right_hip", "left_knee",
        #                    "right_knee", "left_ankle", "right_ankle", "neck"])
        
        self.keypoints = []
        self.depth = depth
        self.orientation : float = None
        self.x : float = None
        self.y : float = None
        for kp in keypoints:
            self.keypoints.append(keypoint(kp.ID, kp.x, kp.y))

        self.left_shoulder =  next((point for point in self.keypoints if point.ID == 5), None)
        self.right_shoulder = next((point for point in self.keypoints if point.ID == 6), None)
        self.left_hip = next((point for point in self.keypoints if point.ID == 11), None)
        self.right_hip = next((point for point in self.keypoints if point.ID == 12), None)
        self.left_ear = next((point for point in self.keypoints if point.ID == 3), None)
        self.right_ear = next((point for point in self.keypoints if point.ID == 4), None)
    
    def getPersonOrientation(self):
        '''Brief: do the check which keypoints are present, then calculate orientation'''
        if(self.left_shoulder and self.right_shoulder):
            self.getOrientationFromPoints(self.left_shoulder,self.right_shoulder)
            return
        if(self.left_hip and self.right_hip):
            self.getOrientationFromPoints(self.left_hip,self.right_hip)
            return
        if(self.left_ear and self.right_ear):
            self.getOrientationFromPoints(self.left_ear,self.right_ear)
            return



    def getOrientationFromPoints(self,left,right):
            left.calculate3DPoint(self.depth)
            right.calculate3DPoint(self.depth)
            self.orientation=np.arctan2(left.y-right.y,left.x-right.x)-np.pi/2

    def getPersonPosition(self):
        kpx = []
        kpy = []
        for kp in self.keypoints:
            tempx, tempy = calculate3DPoint(depth=self.depth,xImage=kp.xImage, yImage=kp.yImage)
            kpx.append(tempx)
            kpy.append(tempy)

        self.x=sum(kpx)/len(kpx)
        self.y=sum(kpy)/len(kpy)




class person_tracking:
    def __init__(self, x, y, theta):
        

        self.x = x
        self.y = y
        self.theta = theta
        self.xdot=None
        self.ydot=None
        self.thetadot=None

    def calculate3DPose(self):
        None
    def calculateOrientation(self):
        None
    def calculatePosition(self):
        None
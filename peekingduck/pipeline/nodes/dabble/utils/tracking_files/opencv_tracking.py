# Copyright 2021 AI Singapore
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Tracking algorithm that uses OpenCV
"""

from typing import Any, Dict, List
import numpy as np
import cv2
from .iou_tracker.utils import format_boxes
from .iou_tracker.utils import iou


trackerTypes = ['BOOSTING', 'MIL', 'KCF', 'TLD', 'MEDIANFLOW', 'GOTURN', 'MOSSE', 'CSRT']


class OpenCVTracker:
    """Native OpenCV tracker that is initialized on bounding boxes detected
    in first frame of video feed.

    Only the "MOSSE" tracker can be selected as it operates at a high FPS.

    References:

    Inference code adapted from:
        https://learnopencv.com/object-tracking-using-opencv-cpp-python/
    """
    def __init__(self) -> None:
        super().__init__()
        self.tracker_type = "MOSSE"
        self.first_frame_or_not = True
        self.next_object_id = 0
        self.iou_thresh = 0.1
        self.tracking_dict = dict() # Dict to store {id (key): [Tracker, bbox(prev)]}

    def run(self, inputs: Dict[str, Any]) -> List[int]:
        """Initialize and update tracker on each frame"""
        frame = np.copy(inputs["img"])
        original_h, original_w, _ = frame.shape
        # Format bboxes from normalized to frame axis
        bboxes = np.copy(inputs["bboxes"])
        bboxes = format_boxes(bboxes, original_h, original_w)
        track_id = []

        # Read the first frame and initialize trackers. The single object
        # tracker is initialized using the first frame and the bounding
        # box indicating the location of the object we want to track
        if self.first_frame_or_not:
            for bbox in bboxes:
                self._initialize_tracker(bbox, frame)
            track_id = list(self.tracking_dict.keys())
            obj_tags = [str(x) for x in track_id]
            self.first_frame_or_not = False

        # Continuous frames
        else:
            obj_tags = self._if_new_bbox_add_track(bboxes, frame)

        # Get updated location of objects in subsequent frames
        for id, tracker in self.tracking_dict.copy().items():
            success, bbox = tracker[0].update(frame)
            if success:
                # update bounding box
                self.tracking_dict.update({id: [tracker[0], bbox]})
            else:
                del self.tracking_dict[id]

        return obj_tags


    def _if_new_bbox_add_track(self, bboxes: List[float], frame: np.array) -> List[int]:
        """Check for new bboxes added and initialize new tracker"""
        prev_frame_tracked_bbox = []
        matching_dict = dict()  # Dict to store {current frame bbox: highest_iou_index}
        # Get previous frames' tracked bboxes
        for _, value in self.tracking_dict.items():
            prev_frame_tracked_bbox.append(np.array(value[1]))

        for box in bboxes:
            # Get matching ious for each bbox in frame to previous bboxes
            ious = iou(np.array(box), np.array(prev_frame_tracked_bbox))
            # Check if current bbox passes iou_thresh with any previous
            # tracked bboxes and get index of highest iou above threshold
            prev_frame_bbox_highest_iou_index = \
                ious.argmax() if round(max(ious), 1) >= self.iou_thresh else None
            matching_dict.update(
                {tuple(box): prev_frame_bbox_highest_iou_index})

        # Create object tags from highest IOU index and tracking_dict
        track_id = []
        for k, v in matching_dict.items():
            if v is not None:
                # Get object ID through prev_frame_bbox_highest_iou_index
                id = list(self.tracking_dict)[v]
                track_id.append(str(id))
            else:
                # Create new tracker for bbox that < IOU threshold
                self._initialize_tracker(k, frame)
                id = list(self.tracking_dict)[-1]
                track_id.append(str(id))
        # Create result list to replace duplicate track_ids
        obj_tags = []
        [obj_tags.append(x) if x not in obj_tags else obj_tags.append("") for x in track_id]

        return obj_tags

    def _initialize_tracker(self,
                            bbox: List[float],
                            frame: np.array) -> Dict[int, List[Any]]:
        """Start a tracker for each bbox"""
        tracker = self._create_tracker_by_name(self.tracker_type)
        tracker.init(frame, tuple(bbox))
        self.next_object_id += 1
        self.tracking_dict.update({self.next_object_id: [tracker, bbox]})
        return self.tracking_dict

    def _create_tracker_by_name(self, trackerType: str) -> Any:
        """Create tracker based on tracker name"""
        if trackerType == trackerTypes[0]:
            tracker = cv2.TrackerBoosting_create()
        elif trackerType == trackerTypes[1]:
            tracker = cv2.TrackerMIL_create()
        elif trackerType == trackerTypes[2]:
            tracker = cv2.TrackerKCF_create()
        elif trackerType == trackerTypes[3]:
            tracker = cv2.TrackerTLD_create()
        elif trackerType == trackerTypes[4]:
            tracker = cv2.TrackerMedianFlow_create()
        elif trackerType == trackerTypes[5]:
            tracker = cv2.TrackerGOTURN_create()
        elif trackerType == trackerTypes[6]:
            tracker = cv2.TrackerMOSSE_create()
        elif trackerType == trackerTypes[7]:
            tracker = cv2.TrackerCSRT_create()
        else:
            tracker = None
        return tracker

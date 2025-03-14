# Copyright 2022 AI Singapore
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
A modular Python framework for Computer Vision Inference.
"""

__version__ = "1.4.0"

import os
import sys

from peekingduck.utils.logger import LoggerSetup
from peekingduck.utils.requirement_checker import RequirementChecker

LoggerSetup()

if "READTHEDOCS" not in os.environ:
    sys.meta_path.insert(0, RequirementChecker())

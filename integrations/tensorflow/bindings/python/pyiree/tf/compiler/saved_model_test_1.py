# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import importlib
import os
import sys
import tempfile
from tensorflow import keras
from pyiree.tf import compiler

# Dynamically import tensorflow.
try:
  # Use a dynamic import so as to avoid hermetic dependency analysis
  # (i.e. we only want the tensorflow from the environment).
  tf = importlib.import_module("tensorflow")
  # Just in case if linked against a pre-V2 defaulted version.
  if hasattr(tf, "enable_v2_behavior"):
    tf.enable_v2_behavior()
  tf = tf.compat.v2
except ImportError:
  print("Not running tests because tensorflow is not available")
  sys.exit(0)

def get_input_shape(data, model):
 if data == 'imagenet':
   if (model == 'InceptionV3' or model == 'Xception' or
       model == 'InceptionResNetV2'):
     return (1, 299, 299, 3)
   elif model == 'NASNetLarge':
     return (1, 331, 331, 3)
   else:
     return (1, 224, 224, 3)
 elif data == 'cifar10':
   return (1, 32, 32, 3)
 else:
   raise ValueError('Not supported data ', data)


def run():
  with tempfile.TemporaryDirectory() as temp_dir:
    input_shape = get_input_shape("imagenet", "MobileNetV2")
    model = tf.keras.applications.MobileNetV2(weights="imagenet", input_shape=tuple(input_shape[1:]))
    i_module = tf.Module()
    i_module.model = model
    i_module.predict = tf.function(
        input_signature=[
          tf.TensorSpec(input_shape, model.inputs[0].dtype)]) (lambda x: model.call(x, training=False))
    sm_dir = os.path.join(temp_dir, "resnet.sm")
    tf.saved_model.save(i_module, sm_dir)

    input_module = compiler.tf_load_saved_model(sm_dir, exported_names=["predict"])
    xla_asm = input_module.to_asm()
    with open("/home/denis/iree-android-demo/third_party/iree/mobilenet.mlir", "w+") as file:
      file.write(xla_asm)

if __name__ == "__main__":
  run()

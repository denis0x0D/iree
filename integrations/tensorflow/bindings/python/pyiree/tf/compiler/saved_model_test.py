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


class StatelessModule(tf.Module):

  def __init__(self):
    pass

  @tf.function(input_signature=[
      tf.TensorSpec([4], tf.float32),
      tf.TensorSpec([4], tf.float32)
  ])
  def add(self, a, b):
    return tf.tanh(a + b)


class RuntimeTest(tf.test.TestCase):

  def testLoadSavedModelToXlaPipeline(self):
    """Tests that a basic saved model to XLA workflow grossly functions.

    This is largely here to verify that everything is linked in that needs to be
    and that there are not no-ops, etc.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
      sm_dir = os.path.join(temp_dir, "simple.sm")
      print("Saving to:", sm_dir)
      my_module = StatelessModule()
      options = tf.saved_model.SaveOptions(save_debug_info=True)
      tf.saved_model.save(my_module, sm_dir, options=options)

      # Load it up.
      input_module = compiler.tf_load_saved_model(sm_dir)
      xla_asm = input_module.to_asm()
      print("XLA ASM:", xla_asm)
      self.assertRegex(xla_asm, "xla_hlo.tanh")

  def testLoadSignatureDefSavedModel(self):
    """Tests loading a SignatureDef saved model with a single variable."""

    with tempfile.TemporaryDirectory() as temp_dir:
      sm_dir = os.path.join(temp_dir, "simple.sm")
      print("Saving to:", sm_dir)

      with tf.Graph().as_default() as graph:
        v = tf.Variable(10)
        result = v.read_value()
        tensor_info = tf.compat.v1.saved_model.utils.build_tensor_info(result)
        sig = tf.compat.v1.saved_model.signature_def_utils.build_signature_def(
            inputs={}, outputs={"result": tensor_info}, method_name="foo")
        builder = tf.compat.v1.saved_model.Builder(sm_dir)
        with tf.compat.v1.Session(graph=graph) as sess:
          sess.run(v.initializer)
          builder.add_meta_graph_and_variables(
              sess, ["bar"], {"baz": sig}, strip_default_attrs=True)
          builder.save()

      module = compiler.tf_load_signature_def_saved_model(
          sm_dir, tags=set(["bar"]), exported_names=["baz"])

      module_asm = module.to_asm(large_element_limit=100)
      self.assertRegexpMatches(module_asm, "flow.variable @[^ ]* dense<10>")


if __name__ == "__main__":
  tf.test.main()

// Copyright 2019 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include "iree/compiler/Dialect/VM/Target/Bytecode/BytecodeModuleTarget.h"
#include "iree/compiler/Dialect/VM/Target/Bytecode/TranslationFlags.h"
#include "mlir/IR/Module.h"
#include "mlir/IR/Visitors.h"
#include "mlir/Translation.h"

namespace mlir {
namespace iree_compiler {
namespace IREE {
namespace VM {

void registerToVMBytecodeTranslation() {
  TranslateFromMLIRRegistration toBytecodeModule(
      "iree-vm-ir-to-bytecode-module",
      [](mlir::ModuleOp moduleOp, llvm::raw_ostream &output) {
        return translateModuleToBytecode(
            moduleOp, getBytecodeTargetOptionsFromFlags(), output);
      });
}

}  // namespace VM
}  // namespace IREE
}  // namespace iree_compiler
}  // namespace mlir

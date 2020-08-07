// Copyright 2020 Google LLC
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

#include "iree/compiler/Dialect/HAL/Target/LLVM/LLVMAOTTargetLinker.h"

#include "iree/base/status.h"
#include "llvm/Support/ToolOutputFile.h"

namespace mlir {
namespace iree_compiler {
namespace IREE {
namespace HAL {

iree::StatusOr<std::string> linkLLVMAOTObjects(
    const std::string& linkerToolPath, const std::string& objData) {
  llvm::SmallString<32> objFilePath, dylibFilePath;
  if (std::error_code error = llvm::sys::fs::createTemporaryFile(
          "llvmaot_dylibs", "objfile", objFilePath)) {
    return iree::InternalErrorBuilder(IREE_LOC)
           << "Failed to generate temporary file for objfile : '"
           << error.message() << "'";
  }
  if (std::error_code error = llvm::sys::fs::createTemporaryFile(
          "llvmaot_dylibs", "dylibfile", dylibFilePath)) {
    return iree::InternalErrorBuilder(IREE_LOC)
           << "Failed to generate temporary file for dylib : '"
           << error.message() << "'";
  }
  std::error_code error;
  auto outputFile = std::make_unique<llvm::ToolOutputFile>(
      objFilePath, error, llvm::sys::fs::F_None);
  if (error) {
    return iree::InternalErrorBuilder(IREE_LOC)
           << "Failed to open temporary objfile '" << objFilePath.c_str()
           << "' for dylib : '" << error.message() << "'";
  }

  outputFile->os() << objData;
  outputFile->os().flush();

  std::string otherOptions =
      " -L/home/denis/ANDROID_SDK/ndk/21.3.6528147/toolchains/llvm/prebuilt/"
      "linux-x86_64/sysroot/usr/lib/aarch64-linux-android/29/ ";

  std::string otherOptions2 =
      " -L/home/denis/ANDROID_SDK/ndk/21.3.6528147/toolchains/llvm/prebuilt/"
      "linux-x86_64/sysroot/usr/lib/aarch64-linux-android/ ";

  std::string otherOptions3 =
      " -L/home/denis/ANDROID_SDK/ndk/21.3.6528147/toolchains/llvm/prebuilt/"
      "linux-x86_64/lib/gcc/aarch64-linux-android/"
      "4.9.x/";

  //  std::string OptionMem =
  //     " /home/denis/iree-android-demo/third_party/iree/memset.o ";

  auto linkingCmd =
      (linkerToolPath + " -shared " + objFilePath + " -o " + dylibFilePath +
       otherOptions + otherOptions2 + otherOptions3 +
       "  -Bstatic -lc++ -Bdynamic -lm -lgcc -lc -lgcc ")
          .str();
  int systemRet = system(linkingCmd.c_str());
  if (systemRet != 0) {
    return iree::InternalErrorBuilder(IREE_LOC)
           << linkingCmd << " failed with exit code " << systemRet;
  }

  auto dylibData = llvm::MemoryBuffer::getFile(dylibFilePath);
  if (!dylibData) {
    return iree::InternalErrorBuilder(IREE_LOC)
           << "Failed to read temporary dylib file '" << dylibFilePath.c_str()
           << "'";
  }
  return dylibData.get()->getBuffer().str();
}

iree::StatusOr<std::string> linkLLVMAOTObjectsWithLLDElf(
    const std::string& objData) {
  return iree::UnimplementedErrorBuilder(IREE_LOC)
         << "linkLLVMAOTObjectsWithLLD not implemented yet!";
}

}  // namespace HAL
}  // namespace IREE
}  // namespace iree_compiler
}  // namespace mlir

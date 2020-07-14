#! /bin/bash

#
# CK post installation script for Glow compiler.
#
# See CK LICENSE.txt for licensing details.
# See CK COPYRIGHT.txt for copyright details.
#

# Environment variables defined by CK:
# PACKAGE_DIR - where the package source files are (under $CK_REPOS/ck-openvino).
# INSTALL_DIR - where the libraries, binaries, etc. are to be deployed (under $CK_TOOLS).

function exit_if_error() {
  message=${1:-"unknown"}
  if [ "${?}" != "0" ]; then
    echo "Error: ${message}!"
    exit 1
  fi
}


export SRC_DIR=${INSTALL_DIR}/glow
export BUILD_DIR=${INSTALL_DIR}/build

# Update the submodules
echo "Updating submodules ..."
cd ${SRC_DIR}
git submodule update --init --recursive

# Create the build dir
cd ${INSTALL_DIR}

if [ ! -d build ] ; then
  mkdir build
fi


# Configure the package.
read -d '' CMK_CMD <<EO_CMK_CMD
${CK_ENV_TOOL_CMAKE_BIN}/cmake \
  -G Ninja
  -DCMAKE_C_COMPILER="${CK_CC_PATH_FOR_CMAKE}" \
  -DCMAKE_C_FLAGS="${CK_CC_FLAGS_FOR_CMAKE} ${EXTRA_FLAGS} -lpthread" \
  -DCMAKE_CXX_COMPILER="${CK_CXX_PATH_FOR_CMAKE}" \
  -DCMAKE_CXX_FLAGS="${CK_CXX_FLAGS_FOR_CMAKE} ${EXTRA_FLAGS} -lpthread" \
  -DCMAKE_AR="${CK_AR_PATH_FOR_CMAKE}" \
  -DCMAKE_RANLIB="${CK_RANLIB_PATH_FOR_CMAKE}" \
  -DCMAKE_LINKER="${CK_LD_PATH_FOR_CMAKE} -lpthread" \
  -DCMAKE_BUILD_TYPE=Release \
  -DGLOG_LIBRARY=${CK_ENV_LIB_GLOG_LIB} \
  -DGLOG_INCLUDE_DIR=${CK_ENV_LIB_GLOG_LIB}/../${CK_ENV_LIB_GLOG_INCLUDE} \
  -Dfmt_DIR=${CK_ENV_LIB_FMT_OBJ_DIR} \
  -DBOOST_INCLUDEDIR=${CK_ENV_LIB_BOOST_INCLUDE} \
  -DBOOST_LIBRARYDIR==${CK_ENV_LIB_BOOST_LIB} \
  -DLLVM_DIR=/usr/lib64/llvm/ \
  "${SRC_DIR}"
EO_CMK_CMD


# First, print the EXACT command we are about to run
echo "Configuring the package with 'CMake' ..."
echo ${CMK_CMD}

echo


# Now, run it from the build directory.
cd ${BUILD_DIR} && eval ${CMK_CMD}
exit_if_error "CMake failed"


# Now, run the ninja command to build
eval ninja all -j8
exit_if_error "ninja all"

return 0



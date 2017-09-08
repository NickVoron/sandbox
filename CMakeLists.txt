cmake_minimum_required(VERSION 3.6)

get_filename_component(ProjectId ${CMAKE_CURRENT_SOURCE_DIR} NAME)
string(REPLACE " " "_" ProjectId ${ProjectId})
project(${ProjectId})

# set PCH for VS project
function(set_target_precompiled_header Target PrecompiledHeader PrecompiledSource)
  if(MSVC)
     set_target_properties(${Target} PROPERTIES COMPILE_FLAGS "/Yu${PrecompiledHeader}")
     set_source_files_properties(${PrecompiledSource} PROPERTIES COMPILE_FLAGS "/Yc${PrecompiledHeader}")
  endif(MSVC)
endfunction(set_target_precompiled_header)

# ignore PCH for a specified list of files
function(ignore_precompiled_header SourcesVar)
  if(MSVC)  
    set_source_files_properties(${${SourcesVar}} PROPERTIES COMPILE_FLAGS "/Y-")
  endif(MSVC)
endfunction(ignore_precompiled_header)

macro(SUBDIRLIST result curdir)
  file(GLOB children RELATIVE ${curdir} ${curdir}/*)
  set(dirlist "")
  foreach(child ${children})
    if(IS_DIRECTORY ${curdir}/${child})
      if(EXISTS ${curdir}/${child}/CMakeLists.txt)
        add_subdirectory(${child})
      endif() 
    endif()
  endforeach()
  set(${result} ${dirlist}) 
endmacro()

include(CheckCXXSymbolExists)

function(st_check_preprocessor output_variable symbol)
  set(CMAKE_REQUIRED_QUIET OFF)
  check_cxx_symbol_exists(${symbol} "" ${output_variable})
  if(NOT ${output_variable})
    set(${output_variable} 0 CACHE INTERNAL "Have symbol ${symbol}" FORCE)
  endif()
endfunction()

st_check_preprocessor(USE_LINUX __linux__)
st_check_preprocessor(USE_WINDOWS _WIN32)
st_check_preprocessor(USE_APPLE __APPLE__)
st_check_preprocessor(USE_ANDROID __ANDROID__)
st_check_preprocessor(USE_FREEBSD __FreeBSD__)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED on)

include_directories("Stable/Sources/Libraries")
include_directories("third_party/dxsdk/Include")
include_directories("third_party/fbxsdk/include")
include_directories("third_party/include")
include_directories("third_party/include/angle/include")
include_directories("third_party/libfreeimage/src")
include_directories("third_party/openexr")
include_directories("third_party/openexr/Imath")
include_directories("third_party/openexr/IlmImf")
include_directories("third_party/openexr/Iex")
include_directories("third_party/openexr/Half")
include_directories("third_party/openexr/IlmThread")
include_directories("third_party/webrtc/src/")
include_directories("third_party/webrtc/src/webrtc/examples/")

add_definitions(-DFT_DEBUG_LEVEL_ERROR -DFT_DEBUG_LEVEL_TRACE -DFT2_BUILD_LIBRARY)
add_definitions(-DGLEW_STATIC)
add_definitions(-DLIBRAW_NODLL)
add_definitions(-DFREEIMAGE_LIB)
add_definitions(-DUTP_DEBUG_LOGGING=0)
add_definitions(-DDIRECTINPUT_VERSION=0x0800)

if(NOT USE_WINDOWS)
  add_definitions(-DPOSIX)
endif()

add_definitions(-DBOOST_SYSTEM_NO_DEPRECATED -DBOOST_TEST_NO_MAIN)
add_subdirectory("boost-cmake")
set(BOOST_ROOT ${BOOST_SOURCE})

include_directories(${BOOST_ROOT})
include_directories("third_party")
include_directories("Stable/Sources/Libraries")

add_subdirectory("third_party")
add_subdirectory("Stable/Sources/Libraries")


add_library(sharedtec INTERFACE)
target_compile_definitions(sharedtec INTERFACE -DBOOST_SYSTEM_NO_DEPRECATED -DBOOST_TEST_NO_MAIN)
target_link_libraries( sharedtec INTERFACE )
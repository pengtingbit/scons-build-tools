#!/usr/bin/env python

import os
import sys
import SCons
import pprint

## Directory path of this SCons tool
tool_path = os.path.dirname(__file__)
## Relative directory path of the logging preprocessor
preprocessor_path = "../../../modules/log/tools/preprocessor"
## Path of the logging preprocessor
preprocessor = os.path.join(tool_path, preprocessor_path, "preprocessor.py")

## Runs the logging preprocessor.
#
# If the source file is empty, it means that the emitter function filtered it. In
# this case nothing is done.
#
# \param target The target file
# \param source The source file
# \param env The environment
def preprocessorAction(target, source, env):
    if source:
        os.system("python2.7 %s " \
                  "--source=%s "  \
                  "--target=%s "  \
                  "--db-path=%s " \
                  "--db-prefix=%s " \
                  % (env['LOG_PREPROCESSOR'], source[0], 
                     target[0], env['LOG_PREPROCESSOR_DB'], 1))


## Checks if the source file is already preprocessed and filters it if necessary. 
#
# If the source file is already preprocessed, the source file return value will be
# empty. 
#
# \param target The target file
# \param source The source file
# \param env The environment
#
# \return Tuple of the new target and the source file
def preprocessorEmitter(target, source, env):
    newTarget = ""
    newTarget = target
    # Register the database as an additional file which is generated during
    # the build. This also ensures mutual exclusion when compiling in parallel
    # with multiple jobs.
    env.SideEffect(env['LOG_PREPROCESSOR_DB'], target)
    # Ensure that this additional file is deleted, too
    env.Clean(target, env['LOG_PREPROCESSOR_DB'])
    env.Depends(target, source)
    return (newTarget, source)

def build_log_object(env, source, alias='__size'):
    return env.LogObjectFile(env.LogPreProcessed(env.CppPreProcessed(source)))

## Configures the builder of the logging preprocessor.
#
# \param env The environment
def generate(env):
    if not env.has_key("BUILDPATH"):
        print("\nERROR: Please load the 'buildpath' tool before 'log-preprocessor'.\n")
        env.Exit(1)
    
    env['LOG_PREPROCESSOR'] = preprocessor
    env['LOG_PREPROCESSOR_DB'] = os.path.join(env["BUILDPATH"], 'log-preprocessor.db')
    
    builder_cpp_preprocessor = \
        SCons.Script.Builder(
            action = SCons.Action.Action(
                "$CXXCOM -E",
                cmdstr="$CXX_PREPARE_COMSTR"),
            single_source = True,
            emitter = env["BUILDPATH_EMITTER"],
            target_factory = env.fs.Entry,
            src_suffix = ".cpp",
            suffix = ".pp")
    
    builder_logging_preprocessor = \
        SCons.Script.Builder(
            action = SCons.Action.Action(
                preprocessorAction,
                cmdstr="$LOG_PREPROCESSOR_COMSTR"),
            single_source = True,
            emitter = [preprocessorEmitter, env["BUILDPATH_EMITTER"]],
            target_factory = env.fs.Entry,
            src_suffix = ".pp",
            suffix = ".lpp")
    
    build_processed_logging = \
        SCons.Script.Builder(
            action = SCons.Action.Action(
                "$CXX -o $TARGET -x c++ -c $CXXFLAGS $CCFLAGS $_CCCOMCOM $SOURCES",
                cmdstr="$CXXCOMSTR"),
            single_source = True,
            emitter = env["BUILDPATH_EMITTER"],
            target_factory = env.fs.Entry,
            src_suffix = ".lpp",
            suffix = ".o")
    
    env.Append(BUILDERS = {
        'CppPreProcessed': builder_cpp_preprocessor,
        'LogPreProcessed': builder_logging_preprocessor,
        'LogObjectFile': build_processed_logging
    })
    
    env.AddMethod(build_log_object, 'LogObject')


## Checks if all prerequisites are met.
#
# Returns always 'True'.
#
# \param env The environment
#
# \retval True If all prerequisites are met
# \retval False If not all prerequisites are met
def exists(env):
    return True
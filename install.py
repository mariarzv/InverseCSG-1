import os, sys, subprocess
import readline, glob # For autocompleting file path.
import urllib.request
import shutil
import helper

# Logics behind this script: it tries to check if all necessary dependences are
# installed. If any of them is missing, it will attempt to download and install
# them, which may require adding new environment variables. To avoid polluting
# users' environment variables, we will save them into an ENVIRONMENT file and
# load them at the beginning of our scripts.

################################################################################
# Helpers.
################################################################################

# Credit:
# https://stackoverflow.com/questions/6656819/filepath-autocompletion-using-users-input
def AutoComplete(text, state):
  return (glob.glob(text + '*') + [None])[state]

def SaveCustomizedEnvironmentVariables(env_variables, file_path):
  f = open(file_path, 'w')
  f.write('# You can manually change the environment variables below:\n')
  for key, val in env_variables.items():
    f.write('%s: %s\n' % (key, val))

def CheckVersionNumber(version_number, target):
  major, minor, change = version_number.split('.')
  major = int(major)
  minor = int(minor)
  change = int(change)
  target_major, target_minor, target_change = target.split('.')
  target_major = int(target_major)
  target_minor = int(target_minor)
  target_change = int(target_change)
  if major > target_major:
    return True
  if major < target_major:
    return False
  if minor > target_minor:
    return True
  if minor < target_minor:
    return False
  if change >= target_change:
    return True
  else:
    return False
  
def CheckSketch():
  sketch_result = subprocess.getoutput('sketch')
  # The first line should be something like:
  # SKETCH version 1.7.4
  # The following is not a very robust way to check the version number.
  if 'SKETCH version' not in sketch_result:
    return False
  # Now check version number.
  first_line = sketch_result.splitlines()[0]
  _, _, version_number = first_line.strip().split()
  # Expect to see >= 1.7.4.
  if not CheckVersionNumber(version_number, '1.7.4'):
    return False
  # Now Sketch seems working.
  helper.PrintWithGreenColor('Sketch %s seems successfully installed.' %
                       version_number)
  # Save environment variables into files.
  sketch_loc = subprocess.getoutput('whereis sketch')
  env_variables['CSG_SKETCH'] = sketch_loc.strip().split()[1].strip()
  # Auto-complete paths.
  readline.set_completer_delims(' \t\n;')
  readline.parse_and_bind('tab: complete')
  readline.set_completer(AutoComplete)
  while 'CSG_SKETCH_FRONTEND' not in env_variables:
    sketch_frontend_folder = input('Tell us the location of sketch-frontend: ') 
    if not os.path.exists(sketch_frontend_folder):
      print('Folder does not exist. Please try again.')
      continue
    env_variables['CSG_SKETCH_FRONTEND'] = sketch_frontend_folder
  while 'CSG_SKETCH_BACKEND' not in env_variables:
    sketch_backend_folder = input('Tell us the location of sketch-backend: ') 
    if not os.path.exists(sketch_backend_folder):
      print('Folder does not exist. Please try again.')
      continue
    env_variables['CSG_SKETCH_BACKEND'] = sketch_backend_folder
  return True

def InstallCGAL():
  helper.Run('sudo apt-get install libcgal-dev')
  helper.PrintWithGreenColor('Installed libcgal-dev')
  cgal_url = 'https://github.com/CGAL/cgal/releases/download/' \
             'releases%2FCGAL-4.12/CGAL-4.12.zip'
  cgal_file = os.path.join(build_folder, 'cgal.zip')
  urllib.request.urlretrieve(cgal_url, cgal_file)
  helper.Run('unzip -o -q %s -d %s' % (cgal_file, build_folder))
  os.remove(cgal_file)
  # Now you have the source code.
  helper.PrintWithGreenColor('Downloaded and unzipped CGAL 4.12')
  cgal_dir = ''
  for folder_name in os.listdir(build_folder):
    if 'cgal' in folder_name or 'CGAL' in folder_name:
      cgal_dir = os.path.join(build_folder, folder_name)
      break
  # Add cgal_root to the environment variable list.
  env_variables['CGAL_DIR'] = os.environ['CGAL_DIR'] = cgal_dir

def InstallEigen():
  helper.Run('wget http://bitbucket.org/eigen/eigen/get/3.3.4.zip')
  cpp_lib_folder = os.path.join(root_folder, 'cpp', 'lib')
  helper.Run('unzip 3.3.4.zip -d %s' % os.path.join(cpp_lib_folder))
  helper.Run('mv %s %s' % (os.path.join(cpp_lib_folder,
    'eigen-eigen-5a0156e40feb'), os.path.join(cpp_lib_folder, 'eigen-3.3.4')))
  helper.Run('rm 3.3.4.zip')
  helper.PrintWithGreenColor('Installed Eigen')

def InstallJava():
  #helper.Run('sudo add-apt-repository -y ppa:webupd8team/java')
  #helper.Run('sudo apt-get update')
  helper.Run('sudo apt-get install oracle-java8-installer')
  # Currently JAVA_HOME is hard coded.
  java_home = '/usr/lib/jvm/java-8-oracle/' 
  env_variables['JAVA_HOME'] = os.environ['JAVA_HOME'] = java_home
  path = os.path.join(java_home, 'bin') + ':' + os.environ['PATH']
  env_variables['PATH'] = os.environ['PATH'] = path
  helper.Run('%s -version' % os.path.join(java_home, 'bin', 'javac'))

def InstallMaven():
  maven_url = 'http://mirrors.koehn.com/apache/maven/maven-3/3.5.3/' \
              'binaries/apache-maven-3.5.3-bin.zip'
  maven_file = os.path.join(build_folder, 'maven.zip')
  urllib.request.urlretrieve(maven_url, maven_file)
  helper.Run('unzip -q %s -d %s' % (maven_file, build_folder))
  os.remove(maven_file)
  # Add it to the environment variable.
  for folder_name in os.listdir(build_folder):
    if 'maven' in folder_name:
      maven_loc = os.path.join(build_folder, folder_name, 'bin')
      env_variables['PATH'] = os.environ['PATH'] \
                            = maven_loc + ':' + os.environ['PATH']
  # Check maven.
  helper.Run('mvn -v')

################################################################################
# Variables.
################################################################################
env_variables = {}

################################################################################
# Beginning of the script.
################################################################################
# Usage: python3 install.py <build folder>
if len(sys.argv) < 2:
  print('Usage: python3 install.py <build_folder>')
  sys.exit(-1)

build_folder = os.path.realpath(sys.argv[1])
root_folder = os.path.dirname(os.path.realpath(sys.argv[0]))
if not os.path.exists(build_folder):
  os.makedirs(build_folder)
helper.PrintWithGreenColor('Build folder created.')

# Add a new environment variable to save the location of the root folder.
env_variables['CSG_ROOT'] = os.environ['CSG_ROOT'] = root_folder

# Check all C++ dependencies.
print('Attempt to install build-essential, autoconf, libtool, flex, bison, '
      'mecurial, zsh, and cmake. Asking for sudo privilege.')
# This works for Ubuntu 17.04 and 16.04.
exit_code = helper.Run('sudo apt-get install gcc-6 g++-6 -y', None)
if exit_code != 0:
  # This works for Ubuntu 14.04.
  helper.Run('sudo apt-get update')
  helper.Run('sudo apt-get install build-essential ' \
    'software-properties-common -y')
  helper.Run('sudo add-apt-repository ppa:ubuntu-toolchain-r/test -y')
  helper.Run('sudo apt-get update')
  helper.Run('sudo apt-get install gcc-snapshot -y')
  helper.Run('sudo apt-get update')
  helper.Run('sudo apt-get install gcc-6 g++-6 -y')
  helper.Run('sudo apt-get install autoconf libtool flex bison '
    'mercurial zsh cmake')

# Install python dependencies.
helper.Run('python -m pip install numpy scipy matplotlib ipython '
           'jupyter pandas sympy nose')
helper.Run('pip install -U scikit-learn')

# Install CGAL.
InstallCGAL()

# Install Eigen-3.3.4.
InstallEigen()

# Compile cpp.
cpp_build_folder = os.path.join(build_folder, 'cpp')
if not os.path.exists(cpp_build_folder):
  os.makedirs(cpp_build_folder)
os.chdir(cpp_build_folder)
os.environ['CC'] = '/usr/bin/gcc-6'
os.environ['CXX'] = '/usr/bin/g++-6'
helper.Run('cmake -DCGAL_DIR=%s %s' % (env_variables['CGAL_DIR'], \
                                       os.path.join(root_folder, 'cpp')))
helper.Run('make')
helper.PrintWithGreenColor('C++ program compiled successfully.')
env_variables['CSG_CPP_EXE'] = os.path.join(cpp_build_folder,
                                            'csg_cpp_command')

# Install Sketch.
# Try calling Sketch. If it is successful, we are done.
if CheckSketch():
  SaveCustomizedEnvironmentVariables(env_variables, os.path.join(
    build_folder, 'ENVIRONMENT'))
  helper.PrintWithGreenColor('Installation Done.')
  sys.exit(0)

# If we are here, Sketch is not properly installed.
# First, install Oracle JDK 8.
print('Attempt to install Oracle JDK 8. Asking for sudo privilege.')
InstallJava()

# Next, install maven.
InstallMaven()

# Download sketch-backend.
sketch_folder = os.path.join(build_folder, 'sketch')
if not os.path.exists(sketch_folder):
  os.makedirs(sketch_folder)
# Sketch-backend.
os.chdir(sketch_folder)
helper.Run('hg clone https://bitbucket.org/gatoatigrado/sketch-backend')
helper.Run('mv sketch-backend sketch-backend-default')
# Use this version of sketch.
helper.Run('hg clone -r 04b3403 sketch-backend-default sketch-backend')
sketch_backend_folder = os.path.join(sketch_folder, 'sketch-backend')
env_variables['CSG_SKETCH_BACKEND'] = sketch_backend_folder
os.chdir(sketch_backend_folder)
helper.Run('bash autogen.sh')
helper.Run('./configure')
helper.Run('make -j2')
# Interestingly, I need to manually do the following copy and paste work to
# avoid an error in sketch-frontend.
sketch_solver_folder = os.path.join(sketch_backend_folder, 'src/SketchSolver')
shutil.copyfile(os.path.join(sketch_solver_folder, 'libcegis.a'), \
                os.path.join(sketch_solver_folder, '.libs/libcegis.a'))
shutil.copyfile(os.path.join(sketch_solver_folder, 'cegis'), \
                os.path.join(sketch_solver_folder, '.libs/cegis'))

# Download sketch-frontend.
os.chdir(sketch_folder)
helper.Run('hg clone https://bitbucket.org/gatoatigrado/sketch-frontend')
helper.Run('mv sketch-frontend sketch-frontend-default')
# Use this version of sketch.
helper.Run('hg clone -r 42c057c sketch-frontend-default sketch-frontend')
sketch_frontend_folder = os.path.join(sketch_folder, 'sketch-frontend')
env_variables['CSG_SKETCH_FRONTEND'] = sketch_frontend_folder
os.chdir(sketch_frontend_folder)
helper.Run('make system-install DESTDIR=/usr/bin SUDOINSTALL=1')

# Now check Sketch again.
if not CheckSketch():
  helper.PrintWithRedColor('Failed to install Sketch. Please fix.')
  sys.exit(-1)

SaveCustomizedEnvironmentVariables(env_variables, os.path.join(
  build_folder, 'ENVIRONMENT'))
helper.PrintWithGreenColor('Installation Done.')
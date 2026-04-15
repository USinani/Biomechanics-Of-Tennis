function setup_matlab_v2_path
%SETUP_MATLAB_V2_PATH Add all Matlab_v2 subfolders to MATLAB path.
here = fileparts(mfilename('fullpath'));
root = fileparts(here);
addpath(genpath(root));
end

function exp_mujoco_benchmark
%EXP_MUJOCO_BENCH Wrapper: load Python-exported CSV and compare trajectories.
root = fileparts(fileparts(mfilename('fullpath')));
addpath(genpath(root));
benchmark_mujoco_parity;
end

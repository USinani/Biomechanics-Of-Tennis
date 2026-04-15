%% MAIN - Matlab_v2 canonical entry: path + baseline swing simulation
% MATLAB = analytical benchmark; compare to MuJoCo via benchmark_mujoco_parity.
thisdir = fileparts(mfilename('fullpath'));
addpath(genpath(thisdir));

params = default_params();
params.control.tau_amp = 5;
params.control.tau_f_hz = 0.8;
params.control.tau_phase_deg = 30;
params.t_end = 1.0;

[t, x, u_hist, y, metrics] = run_swing_sim(params);
fprintf('Peak end-effector speed: %.4f m/s at t = %.4f s\n', ...
    metrics.peak_ee_speed, metrics.time_peak_ee_speed);
fprintf('Trajectory duration: %.3f s\n', metrics.trajectory_duration_s);

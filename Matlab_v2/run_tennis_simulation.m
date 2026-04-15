%% RUN_TENNIS_SIMULATION - Dispatcher to legacy inverse-dynamics demo
% Torque-driven reference: run main or run_swing_sim (see README.md).
thisdir = fileparts(mfilename('fullpath'));
addpath(genpath(thisdir));
fprintf(['[run_tennis_simulation] Forwarding to legacy/run_tennis_inverse_dynamics_demo.m.\n' ...
    'For open-loop swing benchmark use: main or run_swing_sim(default_params).\n\n']);
run(fullfile(thisdir, 'legacy', 'run_tennis_inverse_dynamics_demo.m'));

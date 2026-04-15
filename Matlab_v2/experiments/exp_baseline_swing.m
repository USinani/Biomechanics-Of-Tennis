function exp_baseline_swing
%EXP_BASELINE_SWING Single run with optional export (toggle in script).
root = fileparts(fileparts(mfilename('fullpath')));
addpath(genpath(root));
params = default_params();
params.control.tau_amp = 5;
params.export.enable = true;
params.export.experiment_name = 'baseline_swing';
params.export.save_plots = true;
run_swing_sim(params);
fprintf('Baseline run complete. See outputs/baseline_swing/<run_id>/\n');
end

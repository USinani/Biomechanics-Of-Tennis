function results = exp_initial_angle_sweep
%EXP_INITIAL_ANGLE_SWEEP Grid on initial shoulder / elbow angles.
root = fileparts(fileparts(mfilename('fullpath')));
addpath(genpath(root));
base = default_params();
base.control.tau_amp = 5;
base.control.tau_f_hz = 0.8;
base.t_end = 0.8;
q1s = deg2rad(linspace(-20, 40, 5));
q2s = deg2rad(linspace(30, 90, 5));
[Q1, Q2] = ndgrid(q1s, q2s);
trials = cell(numel(Q1), 1);
idx = 0;
for i = 1:size(Q1, 1)
    for j = 1:size(Q1, 2)
        idx = idx + 1;
        trials{idx} = struct('q0', [Q1(i, j); Q2(i, j)]);
    end
end
cfg = struct('base_params', base, 'experiment_name', 'initial_angle_sweep', 'trials', {trials});
results = run_batch_experiments(cfg);
peaks = arrayfun(@(r) r.metrics.peak_ee_speed, results);
Z = reshape(peaks, size(Q1));
labels = {'q1 grid index', 'q2 grid index', 'Peak EE speed (m/s)'};
generate_heatmaps(1:size(Z, 1), 1:size(Z, 2), Z, labels, ...
    fullfile(base.output_root, 'initial_angle_sweep'), 'angle_grid_peak_speed');
fprintf('Initial-angle sweep done.\n');
end

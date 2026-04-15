function results = exp_timing_sweep
%EXP_TIMING_SWEEP Elbow onset delay vs peak EE speed (heatmap + batch export).
root = fileparts(fileparts(mfilename('fullpath')));
addpath(genpath(root));
base = default_params();
base.control.type = 'timedelay';
base.control.tau_amp = 5;
base.control.tau_f_hz = 0.8;
base.control.tau_phase_deg = 30;
base.control.shoulder_onset = 0;
delays = linspace(0, 0.04, 9);
trials = cell(numel(delays), 1);
for i = 1:numel(delays)
    trials{i} = struct('control', struct('elbow_onset', delays(i)));
end
cfg = struct('base_params', base, 'experiment_name', 'timing_sweep', 'trials', {trials});
results = run_batch_experiments(cfg);
peaks = arrayfun(@(r) r.metrics.peak_ee_speed, results);
figure;
plot(delays, peaks, 'o-', 'LineWidth', 1.5);
xlabel('Elbow onset delay (s)');
ylabel('Peak EE speed (m/s)');
title('Timing sweep: distal onset delay');
grid on;
labels = {'Elbow onset delay (s)', 'Run index', 'Peak EE speed (m/s)'};
generate_heatmaps(1, delays, peaks(:)', labels, ...
    fullfile(base.output_root, 'timing_sweep'), 'timing_peak_speed');
fprintf('Timing sweep done. Exported runs under outputs/timing_sweep/\n');
end

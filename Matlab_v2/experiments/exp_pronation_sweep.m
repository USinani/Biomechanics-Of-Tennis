function results = exp_pronation_sweep
%EXP_PRONATION_SWEEP Option A: kinematic pronation magnitude vs peak EE speed.
root = fileparts(fileparts(mfilename('fullpath')));
addpath(genpath(root));
base = default_params();
base.control.tau_amp = 5;
base.pronation.enable = true;
base.pronation.onset_s = 0.05;
base.pronation.rise_s = 0.08;
mags = deg2rad(linspace(0, 45, 10));
trials = cell(numel(mags), 1);
for i = 1:numel(mags)
    trials{i} = struct('pronation', struct('enable', true, 'magnitude_rad', mags(i), ...
        'onset_s', 0.05, 'rise_s', 0.08));
end
cfg = struct('base_params', base, 'experiment_name', 'pronation_sweep', 'trials', {trials});
results = run_batch_experiments(cfg);
peaks = arrayfun(@(r) r.metrics.peak_ee_speed, results);
figure;
plot(rad2deg(mags), peaks, 's-', 'LineWidth', 1.5);
xlabel('Pronation magnitude (deg)');
ylabel('Peak EE speed (m/s)');
title('Pronation proxy (Option A) vs peak speed');
grid on;
fprintf('Pronation sweep done.\n');
end

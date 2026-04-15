function results = run_batch_experiments(cfg)
%RUN_BATCH_EXPERIMENTS cfg.base_params, cfg.experiment_name, cfg.trials (cell of override structs).
here = fileparts(mfilename('fullpath'));
addpath(genpath(here));

if ~isfield(cfg, 'base_params')
    error('run_batch_experiments:cfg', 'cfg.base_params required');
end
if ~isfield(cfg, 'experiment_name')
    cfg.experiment_name = 'batch';
end
base = cfg.base_params;
trials = cfg.trials;
if isempty(trials)
    trials = {struct()};
end
if isstruct(trials) && ~iscell(trials)
    ta = trials;
    trials = cell(numel(ta), 1);
    for j = 1:numel(ta)
        trials{j} = ta(j);
    end
end
n = numel(trials);
results = repmat(struct('run_id', [], 'metrics', [], 'params_snapshot', [], 'output_path', []), n, 1);
for i = 1:n
    p = deep_merge(base, trials{i});
    p.export.enable = true;
    p.export.experiment_name = cfg.experiment_name;
    p.export.run_id = build_run_id(sprintf('%s_%03d', cfg.experiment_name, i));
    [~, ~, ~, ~, metrics] = run_swing_sim(p);
    results(i).run_id = p.export.run_id;
    results(i).metrics = metrics;
    results(i).params_snapshot = p;
    results(i).output_path = fullfile(p.output_root, p.export.experiment_name, p.export.run_id);
end
end

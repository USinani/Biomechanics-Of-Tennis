function save_run_bundle(params, t, x, u_hist, y, metrics)
%SAVE_RUN_BUNDLE Write CSV/JSON/MAT and optional plots under outputs/<experiment>/<run_id>/.
ex = params.export;
rid = ex.run_id;
if isempty(rid)
    rid = build_run_id(ex.experiment_name);
end
root = fullfile(params.output_root, ex.experiment_name, rid);
ensure_dir(root);
export_states_csv(fullfile(root, 'states.csv'), t, x);
export_controls_csv(fullfile(root, 'controls.csv'), t, u_hist);
export_derived_outputs_csv(fullfile(root, 'derived_outputs.csv'), t, y);
meta = struct('run_id', rid, 'experiment_name', ex.experiment_name);
export_config_json(fullfile(root, 'config.json'), params, meta);
export_metrics_json(fullfile(root, 'metrics.json'), metrics);
save(fullfile(root, 'summary.mat'), 't', 'x', 'u_hist', 'y', 'metrics', 'params', '-v7');
if isfield(ex, 'save_plots') && ex.save_plots
    generate_plots(t, x, u_hist, y, root, 'run');
end
end

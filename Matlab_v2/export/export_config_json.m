function export_config_json(filepath, params, meta)
%EXPORT_CONFIG_JSON Run metadata + flattened numeric parameters.
if nargin < 3
    meta = struct();
end
cfg = struct();
cfg.run_id = ternary(isfield(meta, 'run_id'), meta.run_id, '');
cfg.timestamp = char(datetime('now', 'Format', 'yyyy-MM-dd''T''HH:mm:ss'));
cfg.experiment_name = ternary(isfield(meta, 'experiment_name'), meta.experiment_name, '');
cfg.model_version = params.model_version;
cfg.notes = ternary(isfield(params, 'notes'), params.notes, '');
cfg.dt = params.dt;
cfg.t_end = params.t_end;
cfg.q0_rad = params.q0(:)';
cfg.qd0_rad_s = params.qd0(:)';
cfg.physics = params.physics;
cfg.control = params.control;
if isfield(params, 'pronation')
    cfg.pronation = params.pronation;
end
if isfield(params, 'trunk')
    cfg.trunk = params.trunk;
end
f = fieldnames(meta);
for i = 1:numel(f)
    if ~isfield(cfg, f{i})
        cfg.(f{i}) = meta.(f{i});
    end
end
txt = jsonencode(cfg);
fid = fopen(filepath, 'w');
if fid < 0
    error('export_config_json:io', 'Could not write %s', filepath);
end
fprintf(fid, '%s', txt);
fclose(fid);
end

function v = ternary(cond, a, b)
if cond
    v = a;
else
    v = b;
end
end
